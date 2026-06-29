"""Interactive application entry point."""

from .chains import RepairAnalysisError, analyze_repair_problem
from .config import ConfigurationError
from .schemas import RepairAnalysis


class InputValidationError(ValueError):
    """Raised when the maintenance issue description is empty."""


def validate_problem(problem: str) -> str:
    """Return a normalized problem description or raise a clear error."""

    normalized_problem = problem.strip()
    if not normalized_problem:
        raise InputValidationError("請輸入故障描述，不可為空。")
    return normalized_problem


def format_numbered_list(items: list[str]) -> str:
    """Format strings as a one-based Markdown numbered list."""

    return "\n".join(
        f"{index}. {item}" for index, item in enumerate(items, start=1)
    )


def format_repair_analysis(analysis: RepairAnalysis) -> str:
    """Format structured analysis as readable Markdown."""

    return f"""## 問題摘要

{analysis.summary}

## 可能原因

{format_numbered_list(analysis.possible_causes)}

## 初步檢查方向

{format_numbered_list(analysis.check_steps)}

## 需要補問的資訊

{format_numbered_list(analysis.questions)}

## 建議處理優先順序

{format_numbered_list(analysis.priority_steps)}"""


def main() -> None:
    """Read a maintenance issue, invoke the chain, and print the analysis."""

    try:
        problem = validate_problem(input("請描述要分析的維修問題："))
        analysis = analyze_repair_problem(problem)
    except EOFError as exc:
        raise SystemExit("錯誤：請輸入故障描述，不可為空。") from exc
    except (
        ConfigurationError,
        InputValidationError,
        RepairAnalysisError,
    ) as exc:
        raise SystemExit(f"錯誤：{exc}") from exc

    print(format_repair_analysis(analysis))


if __name__ == "__main__":
    main()
