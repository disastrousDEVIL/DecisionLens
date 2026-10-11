from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    app_name: str = "DecisionLens"
    api_v1_prefix: str = "/api/v1"
    typesafe_api_key: str | None = None
    typesafe_base_url: str = "https://api.typesafe.ai"
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
    openai_api_key: str | None = None
    openai_decisions_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

