from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    upstage_api_key: SecretStr = Field(default=SecretStr(""))
    upstage_base_url: str = "https://api.upstage.ai/v1"
    upstage_chat_model: str = "solar-pro4"
    max_document_chars: int = 10_000
    max_repair_attempts: int = 1
    max_parse_retries: int = 1
