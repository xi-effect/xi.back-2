from typing import Final

import filetype  # type: ignore[import-untyped]
from filetype.types import image  # type: ignore[import-untyped]

FILE_HEADER_SIZE: Final[int] = 8192

SUPPORTED_IMAGE_FORMATS: list[filetype.Type] = [
    image.Avif(),
    image.Bmp(),
    image.Gif(),
    image.Ico(),
    image.Jpeg(),
    image.Jpx(),
    image.Png(),
    image.Tiff(),
    image.Webp(),
]


def match_filetype(obj: bytes, matchers: list[filetype.Type]) -> filetype.Type | None:
    return filetype.match(obj, matchers)


def match_image_filetype(obj: bytes) -> filetype.Type | None:
    return match_filetype(obj, SUPPORTED_IMAGE_FORMATS)
