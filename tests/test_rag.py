"""Offline tests for repair manual RAG core behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from chromadb.api.client import SharedSystemClient
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from repair_assistant.config import AppConfig
from repair_assistant.rag import (
    INSUFFICIENT_MANUAL_DATA,
    ManualDirectoryError,
    ManualQuestionError,
    NoManualDocumentsError,
    VectorStoreNotFoundError,
    answer_manual_question,
    build_vectorstore,
    format_sources,
    load_manual_documents,
    load_vectorstore,
    split_manual_documents,
    validate_manual_question,
)


class LoadManualDocumentsTests(TestCase):
    def test_loads_markdown_and_text_documents(self) -> None:
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "manual.md").write_text(
                "# 手冊\n卡紙處理",
                encoding="utf-8",
            )
            (directory / "notes.txt").write_text(
                "異音檢查",
                encoding="utf-8",
            )

            documents = load_manual_documents(directory)

        self.assertEqual(len(documents), 2)
        self.assertEqual(
            {document.metadata["filename"] for document in documents},
            {"manual.md", "notes.txt"},
        )
        for document in documents:
            self.assertIn("source", document.metadata)

    def test_ignores_unsupported_file_types(self) -> None:
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "manual.md").write_text(
                "支援內容",
                encoding="utf-8",
            )
            (directory / "manual.pdf").write_text(
                "不應讀取",
                encoding="utf-8",
            )
            (directory / "image.png").write_text(
                "不應讀取",
                encoding="utf-8",
            )

            documents = load_manual_documents(directory)

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].metadata["filename"], "manual.md")

    def test_reports_missing_manual_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing_directory = Path(temp_dir) / "missing"

            with self.assertRaisesRegex(
                ManualDirectoryError,
                "資料夾不存在",
            ):
                load_manual_documents(missing_directory)

    def test_reports_directory_without_supported_documents(self) -> None:
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "manual.pdf").write_text(
                "不支援",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                NoManualDocumentsError,
                r"\.md 或 \.txt",
            ):
                load_manual_documents(directory)


class SplitManualDocumentsTests(TestCase):
    def test_splits_documents_and_preserves_metadata(self) -> None:
        document = Document(
            page_content="卡紙處理步驟。" * 30,
            metadata={
                "source": "data/manuals/manual.md",
                "filename": "manual.md",
            },
        )

        chunks = split_manual_documents(
            [document],
            chunk_size=60,
            chunk_overlap=10,
        )

        self.assertGreater(len(chunks), 1)
        for index, chunk in enumerate(chunks, start=1):
            self.assertEqual(
                chunk.metadata["source"],
                "data/manuals/manual.md",
            )
            self.assertEqual(chunk.metadata["filename"], "manual.md")
            self.assertEqual(chunk.metadata["chunk_index"], index)


class VectorStoreTests(TestCase):
    def setUp(self) -> None:
        self.config = AppConfig(
            api_key="test-key",
            base_url="https://example.test/v1",
            model="test-model",
        )

    def test_build_vectorstore_rebuilds_collection_offline(self) -> None:
        first_store = Mock()
        rebuilt_store = Mock()

        with (
            TemporaryDirectory() as temp_dir,
            patch(
                "repair_assistant.rag.create_embeddings",
                return_value=Mock(),
            ),
            patch(
                "repair_assistant.rag._new_vectorstore",
                side_effect=[first_store, rebuilt_store],
            ),
        ):
            root = Path(temp_dir)
            manuals_dir = root / "manuals"
            manuals_dir.mkdir()
            (manuals_dir / "manual.md").write_text(
                "出紙口卡紙時請先關閉電源。",
                encoding="utf-8",
            )

            chunk_count = build_vectorstore(
                manuals_dir,
                root / "vectorstore",
                config=self.config,
            )

        self.assertEqual(chunk_count, 1)
        first_store.delete_collection.assert_called_once_with()
        rebuilt_store.add_documents.assert_called_once()

    def test_reports_vectorstore_not_built(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                VectorStoreNotFoundError,
                "repair-rag-ingest",
            ):
                load_vectorstore(temp_dir, config=self.config)

    def test_persists_and_loads_real_chroma_store_offline(self) -> None:
        fake_embeddings = DeterministicFakeEmbedding(size=32)

        with (
            TemporaryDirectory() as temp_dir,
            patch(
                "repair_assistant.rag.create_embeddings",
                return_value=fake_embeddings,
            ),
        ):
            root = Path(temp_dir)
            manuals_dir = root / "manuals"
            vectorstore_dir = root / "vectorstore"
            manuals_dir.mkdir()
            (manuals_dir / "manual.md").write_text(
                "出紙口卡紙時，請先關閉設備電源並小心取出殘紙。",
                encoding="utf-8",
            )

            chunk_count = build_vectorstore(
                manuals_dir,
                vectorstore_dir,
                config=self.config,
            )
            chroma_system = None
            try:
                vectorstore = load_vectorstore(
                    vectorstore_dir,
                    config=self.config,
                )
                chroma_system = vectorstore._client._system
                results = vectorstore.similarity_search(
                    "出紙口卡紙",
                    k=1,
                )

                self.assertEqual(chunk_count, 1)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].metadata["chunk_index"], 1)
            finally:
                if chroma_system is not None:
                    chroma_system.stop()
                SharedSystemClient.clear_system_cache()



class ManualAnswerTests(TestCase):
    def test_formats_unique_sources(self) -> None:
        documents = [
            Document(
                page_content="內容一",
                metadata={"source": "manual.md", "chunk_index": 1},
            ),
            Document(
                page_content="重複內容",
                metadata={"source": "manual.md", "chunk_index": 1},
            ),
            Document(
                page_content="內容二",
                metadata={"source": "manual.md", "chunk_index": 2},
            ),
        ]

        result = format_sources(documents)

        self.assertIn("manual.md，chunk 1", result)
        self.assertIn("manual.md，chunk 2", result)
        self.assertEqual(result.count("manual.md，chunk 1"), 1)

    def test_rejects_blank_question(self) -> None:
        with self.assertRaisesRegex(
            ManualQuestionError,
            "請輸入維修手冊問題，不可為空。",
        ):
            validate_manual_question(" \t\n ")

    def test_returns_insufficient_message_without_documents(self) -> None:
        with (
            patch(
                "repair_assistant.rag.retrieve_manual_context",
                return_value=[],
            ),
            patch(
                "repair_assistant.rag.create_manual_qa_chain"
            ) as create_chain_mock,
        ):
            result = answer_manual_question("未知錯誤碼怎麼處理？")

        self.assertIn(INSUFFICIENT_MANUAL_DATA, result)
        self.assertIn("目前沒有找到可引用的手冊段落", result)
        create_chain_mock.assert_not_called()

    def test_answer_uses_retrieved_context_and_programmatic_sources(self) -> None:
        document = Document(
            page_content="請先關閉設備電源，再取出殘紙。",
            metadata={
                "source": "data/manuals/sample_manual.md",
                "chunk_index": 1,
            },
        )
        chain = Mock()
        chain.invoke.return_value = "請先關閉設備電源，再取出殘紙。"

        with (
            patch(
                "repair_assistant.rag.retrieve_manual_context",
                return_value=[document],
            ),
            patch("repair_assistant.rag.load_config"),
            patch(
                "repair_assistant.rag.create_manual_qa_chain",
                return_value=chain,
            ),
        ):
            result = answer_manual_question("出紙口卡紙怎麼處理？")

        invocation = chain.invoke.call_args.args[0]
        self.assertIn(document.page_content, invocation["context"])
        self.assertIn("## 回答", result)
        self.assertIn("data/manuals/sample_manual.md，chunk 1", result)
