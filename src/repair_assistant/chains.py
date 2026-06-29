"""LCEL chain for structured maintenance issue analysis."""

from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from .config import AppConfig, load_config
from .schemas import RepairAnalysis


SYSTEM_PROMPT = """你是一位謹慎、務實的印表機與設備維修助理。
請使用繁體中文，根據使用者提供的故障描述產生結構化維修分析。

注意：
- 不要假裝已經知道真正原因，也不要直接宣稱某個原因一定正確。
- 可能原因請使用「可能」語氣。
- 檢查方向需具體可執行。
- 需要補問的資訊需能協助維修人員縮小問題範圍。
- 建議處理優先順序需從低風險、容易檢查的項目開始。
- 每個清單欄位至少提供 3 筆內容。
- 涉及人身、電氣、燃氣、高溫、高壓或設備損壞風險時，
  應明確提醒停止操作並交由合格人員處理。"""

USER_PROMPT = """只回傳一個符合 RepairAnalysis schema 的 JSON object，
不可加入 Markdown、程式碼區塊或 schema 以外的欄位。

欄位與型別必須完全如下：
- "summary": string
- "possible_causes": 至少 3 筆 string 的 array
- "check_steps": 至少 3 筆 string 的 array
- "questions": 至少 3 筆 string 的 array
- "priority_steps": 至少 3 筆 string 的 array

使用者故障描述：

{problem}"""


class RepairAnalysisError(RuntimeError):
    """Raised when a model response cannot produce a RepairAnalysis."""


def create_repair_analysis_chain(config: AppConfig) -> Runnable:
    """Create a chain that returns a validated RepairAnalysis object."""

    model = ChatOpenAI(
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
        temperature=0,
    )
    structured_model = model.with_structured_output(
        RepairAnalysis,
        method="json_mode",
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ]
    )
    return prompt | structured_model


def analyze_repair_problem(problem: str) -> RepairAnalysis:
    """Analyze a maintenance issue and return validated structured data."""

    chain = create_repair_analysis_chain(load_config())
    try:
        result = chain.invoke({"problem": problem})
    except (OutputParserException, ValidationError) as exc:
        raise RepairAnalysisError(
            "模型回覆無法解析為 RepairAnalysis 結構化格式。"
        ) from exc

    if not isinstance(result, RepairAnalysis):
        raise RepairAnalysisError(
            "模型未回傳有效的 RepairAnalysis 結構化結果。"
        )
    return result
