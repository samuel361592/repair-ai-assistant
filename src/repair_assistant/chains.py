"""LCEL chain for maintenance issue analysis."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_openai import ChatOpenAI

from .config import AppConfig


OUTPUT_SECTIONS = (
    "問題摘要",
    "可能原因",
    "初步檢查方向",
    "需要補問的資訊",
    "建議處理優先順序",
)

SYSTEM_PROMPT = """你是一位謹慎、務實的維修問題分析助手。
你的工作是根據使用者描述，整理可能原因與安全的初步檢查方向。
資訊不足時不可武斷下結論；涉及人身、電氣、燃氣、高溫、高壓或設備損壞風險時，
應明確提醒停止操作並交由合格人員處理。

回覆必須使用繁體中文，並嚴格依照以下五個標題與順序輸出，不可省略、改名或新增標題：
問題摘要
可能原因
初步檢查方向
需要補問的資訊
建議處理優先順序

每個標題下請以精簡條列內容回答。"""

USER_PROMPT = """請分析以下維修問題，並直接依照下列格式回答：

問題摘要
- ...

可能原因
- ...

初步檢查方向
- ...

需要補問的資訊
- ...

建議處理優先順序
- ...

維修問題：

{problem}"""

FORMAT_FALLBACK = """問題摘要
- 模型未能產生符合指定格式的分析結果。

可能原因
- 目前資訊不足，無法可靠判斷。

初步檢查方向
- 請先確認設備狀態；如有安全風險，立即停止操作。

需要補問的資訊
- 請補充設備名稱、型號、異常現象、發生時機及已嘗試的處理。

建議處理優先順序
- 先排除人身與設備安全風險，再補充資訊後重新分析。"""


def ensure_output_format(response: str) -> str:
    """Keep valid model output or return a safe response with all sections."""

    normalized_response = response.strip()
    section_positions = [
        normalized_response.find(section) for section in OUTPUT_SECTIONS
    ]
    has_all_sections_in_order = (
        all(position >= 0 for position in section_positions)
        and section_positions == sorted(section_positions)
    )

    if has_all_sections_in_order:
        return normalized_response
    return FORMAT_FALLBACK


def create_repair_analysis_chain(config: AppConfig) -> Runnable:
    """Create the maintenance issue analysis chain."""

    model = ChatOpenAI(
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ]
    )
    return (
        prompt
        | model
        | StrOutputParser()
        | RunnableLambda(ensure_output_format)
    )
