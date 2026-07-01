"""Core retrieval-augmented generation logic for local repair manuals."""

from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import AppConfig, load_config


SUPPORTED_MANUAL_EXTENSIONS = {".md", ".txt"}
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
COLLECTION_NAME = "repair_manuals"
VECTORSTORE_READY_FILE = ".ready"
INSUFFICIENT_MANUAL_DATA = "目前手冊資料不足，無法確認。"

RAG_SYSTEM_PROMPT = """你是一位謹慎的維修手冊問答助理。

請只根據提供的手冊內容回答使用者問題。

規則：
1. 只能使用手冊內容回答。
2. 如果手冊內容不足，請回答：「目前手冊資料不足，無法確認。」
3. 不要編造手冊沒有提到的錯誤碼、零件、步驟或原因。
4. 回答請使用繁體中文。
5. 若手冊有處理步驟，請整理成條列式。
6. 若涉及安全風險，請提醒停止操作並交由合格維修人員處理。"""

RAG_USER_PROMPT = """手冊內容：
{context}

使用者問題：
{question}"""


class RagError(RuntimeError):
    """Base error for repair manual RAG operations."""


class ManualDirectoryError(RagError):
    """Raised when the configured manual directory does not exist."""


class NoManualDocumentsError(RagError):
    """Raised when no supported manual documents are available."""


class EmbeddingError(RagError):
    """Raised when embeddings or vector store operations fail."""


class VectorStoreNotFoundError(RagError):
    """Raised when the local Chroma vector store has not been built."""


class ManualQuestionError(RagError, ValueError):
    """Raised when a manual question is empty."""


class ManualAnswerError(RagError):
    """Raised when the model cannot answer a manual question."""


def validate_manual_question(question: str) -> str:
    """Return a normalized question or raise a clear validation error."""

    normalized_question = question.strip()
    if not normalized_question:
        raise ManualQuestionError("請輸入維修手冊問題，不可為空。")
    return normalized_question


def load_manual_documents(manuals_dir: str | Path) -> list[Document]:
    """Load UTF-8 Markdown and text manuals as LangChain documents."""

    directory = Path(manuals_dir)
    if not directory.is_dir():
        raise ManualDirectoryError(f"維修手冊資料夾不存在：{directory}")

    manual_paths = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_MANUAL_EXTENSIONS
    )
    if not manual_paths:
        raise NoManualDocumentsError(
            f"維修手冊資料夾中沒有 .md 或 .txt 文件：{directory}"
        )

    documents: list[Document] = []
    for path in manual_paths:
        try:
            content = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            raise RagError(f"無法讀取維修手冊：{path}") from exc

        if content.strip():
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": path.as_posix(),
                        "filename": path.name,
                    },
                )
            )

    if not documents:
        raise NoManualDocumentsError(
            f"維修手冊文件沒有可用內容：{directory}"
        )
    return documents


def split_manual_documents(
    documents: list[Document],
    *,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """Split manuals into chunks while preserving source metadata."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            "；",
            "，",
            " ",
            "",
        ],
    )
    chunks: list[Document] = []
    for document in documents:
        document_chunks = splitter.split_documents([document])
        for chunk_index, chunk in enumerate(document_chunks, start=1):
            chunk.metadata = {
                **document.metadata,
                **chunk.metadata,
                "chunk_index": chunk_index,
            }
            chunks.append(chunk)
    return chunks


def create_embeddings(config: AppConfig) -> OpenAIEmbeddings:
    """Create the configured OpenAI-compatible embedding model."""

    return OpenAIEmbeddings(
        model=config.embedding_model,
        base_url=config.base_url,
        api_key=config.api_key,
    )


def _new_vectorstore(
    vectorstore_dir: str | Path,
    embeddings: Any,
) -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(vectorstore_dir),
    )


def build_vectorstore(
    manuals_dir: str | Path,
    vectorstore_dir: str | Path,
    *,
    config: AppConfig | None = None,
) -> int:
    """Rebuild the local Chroma store and return the chunk count."""

    documents = load_manual_documents(manuals_dir)
    chunks = split_manual_documents(documents)
    if not chunks:
        raise NoManualDocumentsError("維修手冊切片後沒有可建立索引的內容。")

    effective_config = config or load_config()
    persist_path = Path(vectorstore_dir)
    persist_path.mkdir(parents=True, exist_ok=True)
    ready_file = persist_path / VECTORSTORE_READY_FILE
    ready_file.unlink(missing_ok=True)

    try:
        embeddings = create_embeddings(effective_config)
        vectorstore = _new_vectorstore(persist_path, embeddings)
        vectorstore.delete_collection()
        vectorstore = _new_vectorstore(persist_path, embeddings)
        vectorstore.add_documents(chunks)
        ready_file.write_text(COLLECTION_NAME, encoding="utf-8")
    except Exception as exc:
        raise EmbeddingError(
            "建立維修手冊向量庫失敗，請檢查 "
            "OPENAI_EMBEDDING_MODEL 與 OPENAI_BASE_URL 是否支援 Embedding。"
        ) from exc

    return len(chunks)


def load_vectorstore(
    vectorstore_dir: str | Path,
    *,
    config: AppConfig | None = None,
) -> Chroma:
    """Load an existing local Chroma store."""

    persist_path = Path(vectorstore_dir)
    if not (persist_path / VECTORSTORE_READY_FILE).is_file():
        raise VectorStoreNotFoundError(
            "維修手冊向量庫尚未建立，請先執行 uv run repair-rag-ingest。"
        )

    try:
        embeddings = create_embeddings(config or load_config())
        return _new_vectorstore(persist_path, embeddings)
    except Exception as exc:
        raise RagError(f"無法載入維修手冊向量庫：{persist_path}") from exc


def retrieve_manual_context(
    question: str,
    *,
    config: AppConfig | None = None,
    k: int = 4,
) -> list[Document]:
    """Retrieve the most relevant repair manual chunks."""

    normalized_question = validate_manual_question(question)
    effective_config = config or load_config()
    vectorstore = load_vectorstore(
        effective_config.vectorstore_dir,
        config=effective_config,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    try:
        return list(retriever.invoke(normalized_question))
    except Exception as exc:
        raise EmbeddingError(
            "檢索維修手冊失敗，請檢查 embedding model、base URL 與向量庫。"
        ) from exc


def format_manual_context(documents: list[Document]) -> str:
    """Format retrieved chunks for the model prompt."""

    sections = []
    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "未知來源")
        chunk_index = document.metadata.get("chunk_index", "?")
        sections.append(
            f"[來源 {index}：{source}，chunk {chunk_index}]\n"
            f"{document.page_content}"
        )
    return "\n\n".join(sections)


def format_sources(documents: list[Document]) -> str:
    """Format unique document sources without relying on model output."""

    if not documents:
        return "## 來源\n\n目前沒有找到可引用的手冊段落。"

    source_lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for document in documents:
        source = str(document.metadata.get("source", "未知來源"))
        chunk_index = str(document.metadata.get("chunk_index", "?"))
        source_key = (source, chunk_index)
        if source_key in seen:
            continue
        seen.add(source_key)
        source_lines.append(
            f"{len(source_lines) + 1}. {source}，chunk {chunk_index}"
        )
    return "## 來源\n\n" + "\n".join(source_lines)


def create_manual_qa_chain(config: AppConfig) -> Runnable:
    """Create the context-grounded manual QA chain."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", RAG_USER_PROMPT),
        ]
    )
    model = ChatOpenAI(
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
        temperature=0,
    )
    return prompt | model | StrOutputParser()


def answer_manual_question(question: str) -> str:
    """Answer from retrieved manual content and append programmatic sources."""

    normalized_question = validate_manual_question(question)
    documents = retrieve_manual_context(normalized_question)
    if not documents:
        return (
            f"## 回答\n\n{INSUFFICIENT_MANUAL_DATA}\n\n"
            f"{format_sources([])}"
        )

    config = load_config()
    chain = create_manual_qa_chain(config)
    try:
        answer = chain.invoke(
            {
                "context": format_manual_context(documents),
                "question": normalized_question,
            }
        ).strip()
    except Exception as exc:
        raise ManualAnswerError(
            "維修手冊問答失敗，請檢查模型設定與服務狀態。"
        ) from exc

    if not answer:
        answer = INSUFFICIENT_MANUAL_DATA
    return f"## 回答\n\n{answer}\n\n{format_sources(documents)}"
