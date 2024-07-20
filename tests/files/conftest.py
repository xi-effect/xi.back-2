from secrets import choice
from typing import Any

import pytest
from faker import Faker

from app.common.config import ALLOWED_FILE_EXTENSIONS


@pytest.fixture()
async def file_data(faker: Faker) -> dict[str, Any]:
    filename = faker.file_name(extension=choice(ALLOWED_FILE_EXTENSIONS))
    return {
        "filename": filename,
        "file": ("files", (filename, faker.binary(length=1), "multipart/form-data")),
    }


@pytest.fixture()
async def files_data(faker: Faker) -> dict[str, list[Any]]:
    files = [faker.file_name(extension=ext) for ext in ALLOWED_FILE_EXTENSIONS]
    return {
        "filenames": files,
        "files": [
            ("files", (filename, faker.binary(length=1), "multipart/form-data"))
            for filename in files
        ],
    }
