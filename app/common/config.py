from os import getenv
from pathlib import Path

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.common.sqlalchemy_ext import MappingBase, sqlalchemy_naming_convention

current_directory: Path = Path.cwd()

AVATARS_PATH: Path = current_directory / "community_avatars"
STORAGE_PATH: Path = current_directory / "storage"

PRODUCTION_MODE: bool = getenv("PRODUCTION", "0") == "1"

DB_URL: str = getenv("DB_LINK", "postgresql+psycopg://test:test@localhost:5432/test")
DB_SCHEMA: str | None = getenv("DB_SCHEMA", None)
DATABASE_MIGRATED: bool = getenv("DATABASE_MIGRATED", "0") == "1"

LOCAL_PORT: str = getenv("LOCAL_PORT", "8000")

BRIDGE_BASE_URL: str = getenv("BRIDGE_BASE_URL", f"http://localhost:{LOCAL_PORT}")

API_KEY: str = getenv("API_KEY", "local")  # common for now, split later
MUB_KEY: str = getenv("MUB_KEY", "local")

engine = create_async_engine(
    DB_URL,
    echo=not PRODUCTION_MODE,
    pool_recycle=280,
)
db_meta = MetaData(naming_convention=sqlalchemy_naming_convention, schema=DB_SCHEMA)
sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase, MappingBase):
    __tablename__: str
    __abstract__: bool

    metadata = db_meta
