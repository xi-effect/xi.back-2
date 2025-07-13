import sys
from pathlib import Path

from aiosmtplib import SMTP
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.common.cyptography import CryptographyProvider
from app.common.sqlalchemy_ext import MappingBase, sqlalchemy_naming_convention


class FernetSettings(BaseModel):
    current_key: str = Field(default_factory=lambda: Fernet.generate_key().decode())
    backup_key: str | None = None
    encryption_ttl: int

    @computed_field
    @property
    def keys(self) -> list[str]:
        return (
            [self.current_key]
            if self.backup_key is None
            else [self.current_key, self.backup_key]
        )


class EmailSettings(BaseModel):
    hostname: str
    username: str
    password: str
    port: int = 465
    timeout: int = 20
    use_tls: bool = True


class TelegramBotSettings(BaseModel):
    token: str
    webhook_token: str | None = None


class SupbotSettings(TelegramBotSettings):
    group_id: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_ignore_empty=True,
        nested_model_default_partial_update=True,
        extra="ignore",
    )

    production_mode: bool = False

    @computed_field
    @property
    def is_testing_mode(self) -> bool:
        return "pytest" in sys.modules

    api_key: str = "local"  # common for now, split later
    mub_key: str = "local"

    bridge_base_url: str = "http://localhost:5000"

    cookie_domain: str = "localhost"

    password_reset_keys: FernetSettings = FernetSettings(encryption_ttl=60 * 60)
    email_confirmation_keys: FernetSettings = FernetSettings(
        encryption_ttl=60 * 60 * 24
    )
    telegram_connection_token_keys: FernetSettings = FernetSettings(
        encryption_ttl=60 * 5
    )

    demo_webhook_url: str | None = None
    vacancy_webhook_url: str | None = None

    base_path: Path = Path.cwd()
    avatars_folder: Path = Path("avatars")

    @computed_field
    @property
    def avatars_path(self) -> Path:
        return self.base_path / self.avatars_folder

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

    email: EmailSettings | None = None

    supbot: SupbotSettings | None = None
    notifications_bot: TelegramBotSettings | None = None
    telegram_webhook_base_url: str | None = None


settings = Settings()

engine = create_async_engine(
    url=settings.postgres_dsn,
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


smtp_client: SMTP | None = (
    None
    if settings.email is None
    else SMTP(
        hostname=settings.email.hostname,
        username=settings.email.username,
        password=settings.email.password,
        use_tls=settings.email.use_tls,
        port=settings.email.port,
        timeout=settings.email.timeout,
    )
)

password_reset_cryptography = CryptographyProvider(
    settings.password_reset_keys.keys,
    encryption_ttl=settings.password_reset_keys.encryption_ttl,
)
email_confirmation_cryptography = CryptographyProvider(
    settings.email_confirmation_keys.keys,
    encryption_ttl=settings.email_confirmation_keys.encryption_ttl,
)
