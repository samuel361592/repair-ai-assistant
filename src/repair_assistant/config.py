"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


REQUIRED_ENV_VARS = (
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
)


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is missing."""


@dataclass(frozen=True)
class AppConfig:
    """Settings required to create the chat model."""

    api_key: str
    base_url: str
    model: str


def load_config() -> AppConfig:
    """Load and validate settings from the local .env file and environment."""

    load_dotenv()
    values = {
        variable: os.getenv(variable, "").strip()
        for variable in REQUIRED_ENV_VARS
    }
    missing = [variable for variable, value in values.items() if not value]

    if missing:
        missing_names = ", ".join(missing)
        raise ConfigurationError(
            f"缺少必要環境變數：{missing_names}。請在 .env 中完成設定。"
        )

    return AppConfig(
        api_key=values["OPENAI_API_KEY"],
        base_url=values["OPENAI_BASE_URL"],
        model=values["OPENAI_MODEL"],
    )
