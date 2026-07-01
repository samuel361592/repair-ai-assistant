"""Command-line entry points for repair manual RAG ingestion and QA."""

from .config import ConfigurationError, load_config
from .rag import (
    RagError,
    answer_manual_question,
    build_vectorstore,
    load_manual_documents,
    validate_manual_question,
)


def ingest_main() -> None:
    """Build or rebuild the local repair manual vector store."""

    try:
        config = load_config()
        document_count = len(load_manual_documents(config.manuals_dir))
        chunk_count = build_vectorstore(
            config.manuals_dir,
            config.vectorstore_dir,
            config=config,
        )
    except (ConfigurationError, RagError) as exc:
        raise SystemExit(f"錯誤：{exc}") from exc

    print(
        "已建立維修手冊向量庫。\n"
        f"文件數：{document_count}\n"
        f"切片數：{chunk_count}\n"
        f"向量庫位置：{config.vectorstore_dir}"
    )


def qa_main() -> None:
    """Answer one repair manual question using local retrieval."""

    try:
        question = validate_manual_question(
            input("請輸入維修手冊問題：")
        )
        result = answer_manual_question(question)
    except EOFError as exc:
        raise SystemExit("錯誤：請輸入維修手冊問題，不可為空。") from exc
    except (ConfigurationError, RagError) as exc:
        raise SystemExit(f"錯誤：{exc}") from exc

    print(result)


if __name__ == "__main__":
    qa_main()
