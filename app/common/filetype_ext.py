from typing import Final

import filetype  # type: ignore[import-untyped]
from filetype.types import (  # type: ignore[import-untyped]
    archive,
    audio,
    document,
    image,
)

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

SUPPORTED_DOCUMENT_FORMATS: list[filetype.Type] = [
    archive.Pdf(),
]

SUPPORTED_AUDIO_FORMATS: list[filetype.Type] = [
    audio.Aac(),
    audio.Mp3(),
    audio.M4a(),
    audio.Ogg(),
    audio.Flac(),
    audio.Wav(),
]

SUPPORTED_PRESENTATION_FORMATS: list[filetype.Type] = [
    document.Pptx(),
]

PRESENTATION_CONTENT_TYPE: Final[str] = (
    "application/vnd.openxmlformats-officedocument.presentationml.presentation"
)


def match_filetype(obj: bytes, matchers: list[filetype.Type]) -> filetype.Type | None:
    return filetype.match(obj, matchers)


def match_image_filetype(obj: bytes) -> filetype.Type | None:
    return match_filetype(obj, SUPPORTED_IMAGE_FORMATS)


def match_document_filetype(obj: bytes) -> filetype.Type | None:
    return match_filetype(obj, SUPPORTED_DOCUMENT_FORMATS)


def match_audio_filetype(obj: bytes) -> filetype.Type | None:
    return match_filetype(obj, SUPPORTED_AUDIO_FORMATS)


def match_presentation_filetype(obj: bytes) -> filetype.Type | None:
    return match_filetype(obj, SUPPORTED_PRESENTATION_FORMATS)
