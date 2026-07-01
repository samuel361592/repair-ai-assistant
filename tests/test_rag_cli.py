"""Offline tests for repair manual RAG command-line entry points."""

from unittest import TestCase
from unittest.mock import patch

from langchain_core.documents import Document

from repair_assistant.config import AppConfig
from repair_assistant.rag_cli import ingest_main, qa_main


class RagCliTests(TestCase):
    def setUp(self) -> None:
        self.config = AppConfig(
            api_key="test-key",
            base_url="https://example.test/v1",
            model="test-model",
        )

    def test_ingest_main_reports_counts_and_location(self) -> None:
        document = Document(page_content="手冊內容")

        with (
            patch(
                "repair_assistant.rag_cli.load_config",
                return_value=self.config,
            ),
            patch(
                "repair_assistant.rag_cli.load_manual_documents",
                return_value=[document],
            ),
            patch(
                "repair_assistant.rag_cli.build_vectorstore",
                return_value=3,
            ),
            patch("builtins.print") as print_mock,
        ):
            ingest_main()

        output = print_mock.call_args.args[0]
        self.assertIn("文件數：1", output)
        self.assertIn("切片數：3", output)
        self.assertIn(self.config.vectorstore_dir, output)

    def test_qa_main_rejects_blank_question(self) -> None:
        with (
            patch("builtins.input", return_value=" \t "),
            self.assertRaisesRegex(
                SystemExit,
                "請輸入維修手冊問題，不可為空。",
            ),
        ):
            qa_main()

    def test_qa_main_prints_answer(self) -> None:
        with (
            patch("builtins.input", return_value="出紙口卡紙怎麼處理？"),
            patch(
                "repair_assistant.rag_cli.answer_manual_question",
                return_value="## 回答\n\n測試回答",
            ) as answer_mock,
            patch("builtins.print") as print_mock,
        ):
            qa_main()

        answer_mock.assert_called_once_with("出紙口卡紙怎麼處理？")
        print_mock.assert_called_once_with("## 回答\n\n測試回答")
