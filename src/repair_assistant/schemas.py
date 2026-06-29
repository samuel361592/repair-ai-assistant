"""Structured output schemas for maintenance issue analysis."""

from pydantic import BaseModel, Field


class RepairAnalysis(BaseModel):
    """Structured maintenance issue analysis returned by the chat model."""

    summary: str = Field(
        min_length=1,
        description="一句話整理使用者描述的故障問題",
    )
    possible_causes: list[str] = Field(
        min_length=3,
        description="可能原因，至少 3 筆",
    )
    check_steps: list[str] = Field(
        min_length=3,
        description="初步檢查方向，至少 3 筆",
    )
    questions: list[str] = Field(
        min_length=3,
        description="需要補問的資訊，至少 3 筆",
    )
    priority_steps: list[str] = Field(
        min_length=3,
        description="建議處理優先順序，至少 3 筆",
    )
