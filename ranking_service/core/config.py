from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="VibeMatching Ranking Service", alias="RANKING_APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="RANKING_API_V1_PREFIX")
    elasticsearch_enabled: bool = Field(default=False, alias="RANKING_ES_ENABLED")
    elasticsearch_url: str = Field(default="http://localhost:9200", alias="RANKING_ES_URL")
    elasticsearch_profiles_index: str = Field(
        default="profiles", alias="RANKING_ES_PROFILES_INDEX"
    )


settings = Settings()
