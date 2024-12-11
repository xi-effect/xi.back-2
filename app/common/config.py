from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.common.sqlalchemy_ext import MappingBase, sqlalchemy_naming_convention


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_ignore_empty=True,
    )

    api_key: str = "local"  # common for now, split later
    mub_key: str = "local"

    bridge_base_url: str = "http://localhost:8000"

    base_path: Path = Path.cwd()
    community_avatars_folder: Path = Path("community_avatars")

    @computed_field
    @property
    def community_avatars_path(self) -> Path:
        return self.base_path / self.community_avatars_folder

    storage_folder: Path = Path("storage")

    @computed_field
    @property
    def storage_path(self) -> Path:
        return self.base_path / self.storage_folder

    postgres_host: str = "localhost:5432"
    postgres_username: str = "test"
    postgres_password: str = "test"
    postgres_database: str = "test"

    @computed_field
    @property
    def postgres_dsn(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_username}"
            f":{self.postgres_password}"
            f"@{self.postgres_host}"
            f"/{self.postgres_database}"
        )

    postgres_schema: str | None = None
    postgres_automigrate: bool = True
    postgres_echo: bool = True
    postgres_pool_recycle: int = 280

    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"
    livekit_demo_base_url: str = "https://meet.livekit.io/custom"


settings = Settings()

engine = create_async_engine(
    settings.postgres_dsn,
    echo=settings.postgres_echo,
    pool_recycle=settings.postgres_pool_recycle,
)
db_meta = MetaData(
    naming_convention=sqlalchemy_naming_convention,
    schema=settings.postgres_schema,
)
sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase, MappingBase):
    __tablename__: str
    __abstract__: bool

    metadata = db_meta
