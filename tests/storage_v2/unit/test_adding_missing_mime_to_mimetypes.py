import mimetypes

import filetype  # type: ignore[import-untyped]
import pytest

from app.common.filetype_ext import SUPPORTED_AUDIO_FORMATS
from app.storage_v2.utils.mimetypes import SUPPORTED_AUDIO_MIME_TYPES

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "audio_format",
    [pytest.param(audio, id=audio.extension) for audio in SUPPORTED_AUDIO_FORMATS],
)
async def test_matching_extension_by_filetype_mime_types(
    audio_format: filetype.Type,
) -> None:
    assert f".{audio_format.extension}" in mimetypes.guess_all_extensions(
        audio_format.mime
    )


@pytest.mark.parametrize(
    (
        "mime",
        "extension",
    ),
    [
        pytest.param(mime, extension, id=extension)
        for mime, extension in SUPPORTED_AUDIO_MIME_TYPES.items()
    ],
)
async def test_presence_extension_by_mime_types(mime: str, extension: str) -> None:
    assert extension in mimetypes.guess_all_extensions(mime)
