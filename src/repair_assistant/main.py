"""Interactive application entry point."""

from .chains import create_repair_analysis_chain
from .config import ConfigurationError, load_config


class InputValidationError(ValueError):
    """Raised when the maintenance issue description is empty."""


def validate_problem(problem: str) -> str:
    """Return a normalized problem description or raise a clear error."""

    normalized_problem = problem.strip()
    if not normalized_problem:
        raise InputValidationError("維修問題不可為空，請提供設備與異常現象。")
    return normalized_problem


def main() -> None:
    """Read a maintenance issue, invoke the chain, and print the analysis."""

    try:
        config = load_config()
        problem = validate_problem(input("請描述要分析的維修問題："))
    except EOFError as exc:
        raise SystemExit("錯誤：未收到維修問題輸入。") from exc
    except (ConfigurationError, InputValidationError) as exc:
        raise SystemExit(f"錯誤：{exc}") from exc

    chain = create_repair_analysis_chain(config)
    result = chain.invoke({"problem": problem})
    print(result)


if __name__ == "__main__":
    main()
