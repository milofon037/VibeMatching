from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(alias="APP_NAME")
    service_name: str = Field(alias="SERVICE_NAME")
    health_status_ok: str = Field(alias="HEALTH_STATUS_OK")
    app_env: str = Field(alias="APP_ENV")
    debug: bool = Field(alias="DEBUG")
    api_v1_prefix: str = Field(alias="API_V1_PREFIX")

    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_port: int = Field(alias="POSTGRES_PORT")

    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(alias="REDIS_PORT")
    redis_db: int = Field(alias="REDIS_DB")

    rabbitmq_host: str = Field(alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(alias="RABBITMQ_PORT")
    rabbitmq_user: str = Field(alias="RABBITMQ_USER")
    rabbitmq_password: str = Field(alias="RABBITMQ_PASSWORD")

    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(alias="MINIO_BUCKET")
    minio_secure: bool = Field(alias="MINIO_SECURE")
    photo_max_per_profile: int = Field(alias="PHOTO_MAX_PER_PROFILE")
    photo_max_file_size_bytes: int = Field(alias="PHOTO_MAX_FILE_SIZE_BYTES")
    photo_allowed_content_types_raw: str = Field(alias="PHOTO_ALLOWED_CONTENT_TYPES")
    photo_allowed_extensions_raw: str = Field(alias="PHOTO_ALLOWED_EXTENSIONS")
    feed_batch_size: int = Field(alias="FEED_BATCH_SIZE")
    ranking_service_enabled: bool = Field(default=False, alias="RANKING_SERVICE_ENABLED")
    ranking_service_url: str = Field(default="http://localhost:8010", alias="RANKING_SERVICE_URL")
    ranking_service_timeout_seconds: float = Field(
        default=1.5, alias="RANKING_SERVICE_TIMEOUT_SECONDS"
    )
    feed_cache_enabled: bool = Field(default=True, alias="FEED_CACHE_ENABLED")
    feed_cache_batch_size: int = Field(default=10, alias="FEED_CACHE_BATCH_SIZE")
    feed_cache_ttl_seconds: int = Field(default=900, alias="FEED_CACHE_TTL_SECONDS")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def alembic_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg")

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@"
            f"{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )

    @property
    def photo_allowed_content_types(self) -> list[str]:
        return [
            item.strip() for item in self.photo_allowed_content_types_raw.split(",") if item.strip()
        ]

    @property
    def photo_allowed_extensions(self) -> list[str]:
        return [
            item.strip().lower()
            for item in self.photo_allowed_extensions_raw.split(",")
            if item.strip()
        ]


settings = Settings()
