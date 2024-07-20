import os
from pathlib import Path

from faker import Faker

from app.common.config import FILE_STORAGE_PATH, FILE_STORAGE_PATH_MUB
from app.files.models.files_db import File
from tests.common.active_session import ActiveSession


def clear_file_storage(*, mub: bool = False) -> None:
    storage_path = FILE_STORAGE_PATH_MUB if mub else FILE_STORAGE_PATH
    for filename in os.listdir(storage_path):
        Path(storage_path, filename).unlink()


async def create_file(
    session: ActiveSession,
    filename: str,
    data: bytes | None = None,
    *,
    mub: bool = False,
) -> None:
    storage_path = FILE_STORAGE_PATH_MUB if mub else FILE_STORAGE_PATH
    with Path(storage_path, filename).open("wb") as file:
        if data is None:
            file.write(Faker().pystr().encode("utf-8"))
        else:
            file.write(data)
    async with session():
        await File.create(filename=filename)
