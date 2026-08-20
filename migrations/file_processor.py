import itertools
import os
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import UUID

import filetype  # type: ignore[import-untyped]
import sqlalchemy as sa
from filetype.types import archive, audio, image  # type: ignore[import-untyped]
from PIL import Image
from sqlalchemy import bindparam, create_engine

schema_name = "xi_back_2"
table_name = "files"

base_path = Path.cwd()
storage_path = base_path.joinpath("storage")


class FileKind(StrEnum):
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    UNCATEGORIZED = "UNCATEGORIZED"


FILE_KIND_TO_SUPPORTED_FILETYPE: dict[FileKind, list[filetype.Type]] = {
    FileKind.AUDIO: [
        audio.Aac(),
        audio.Mp3(),
        audio.M4a(),
        audio.Ogg(),
        audio.Flac(),
        audio.Wav(),
    ],
    FileKind.IMAGE: [
        image.Avif(),
        image.Bmp(),
        image.Gif(),
        image.Ico(),
        image.Jpeg(),
        image.Jpx(),
        image.Png(),
        image.Tiff(),
        image.Webp(),
    ],
    FileKind.DOCUMENT: [
        archive.Pdf(),
    ],
}

ALL_SUPPORTED_TYPES = list(
    itertools.chain.from_iterable(FILE_KIND_TO_SUPPORTED_FILETYPE.values())
)

FILE_KIND_TO_FOLDER: dict[FileKind, Path] = {
    FileKind.AUDIO: storage_path.joinpath("audios"),
    FileKind.DOCUMENT: storage_path.joinpath("documents"),
    FileKind.IMAGE: storage_path.joinpath("images"),
    FileKind.UNCATEGORIZED: storage_path.joinpath("uncategorized"),
}

engine = create_engine(url="postgresql+psycopg://test:test@db:5432/test")
metadata = sa.MetaData(schema=schema_name)


def match_supported_files(file: os.DirEntry[str]) -> filetype.Type | None:
    return filetype.match(file.path, ALL_SUPPORTED_TYPES)


def save_image_to_webp(file: os.DirEntry[str]) -> None:
    with Image.open(file.path) as img:
        img.save(FILE_KIND_TO_FOLDER[FileKind.IMAGE].joinpath(file.name), format="webp")


def main() -> None:
    data_to_update: list[dict[str, Any]] = []

    with os.scandir(FILE_KIND_TO_FOLDER[FileKind.UNCATEGORIZED]) as files:
        for file in files:
            if not file.is_file():
                continue

            file_type = match_supported_files(file)
            if file_type is None:
                continue

            file_kind: FileKind | None = [
                k for k, v in FILE_KIND_TO_SUPPORTED_FILETYPE.items() if file_type in v
            ][0]

            if file_kind is None:
                continue

            if file_kind is FileKind.IMAGE and not isinstance(file_type, image.Webp):
                save_image_to_webp(file)
                Path(file.path).unlink()
            else:  # todo: Upgrade when adding conversion of other file types (elif)
                Path(file.path).rename(FILE_KIND_TO_FOLDER[file_kind] / file.name)

            data_to_update.append(
                {"file_id": UUID(hex=file.name), "new_kind": file_kind}
            )

    with engine.begin() as conn:
        Files = sa.Table("files", metadata, autoload_with=conn)
        stmt = (
            sa.update(Files)
            .values(kind=bindparam("new_kind"))
            .where(Files.c.id == bindparam("file_id"))
        )
        conn.execute(stmt, data_to_update)
        conn.commit()


if __name__ == "__main__":
    main()
