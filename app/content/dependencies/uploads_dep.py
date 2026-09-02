from collections.abc import Callable
from mimetypes import guess_all_extensions
from typing import Annotated

import filetype  # type: ignore[import-untyped]
from fastapi import Depends, UploadFile
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.common.filetype_ext import (
    FILE_HEADER_SIZE,
    match_audio_filetype,
    match_document_filetype,
    match_image_filetype,
    match_presentation_filetype,
)
from app.content.models.files_db import FileKind


class FileFormatResponses(Responses):
    WRONG_FORMAT = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Invalid file format"
    CONTENT_TYPE_MISMATCH = (
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "File content doesn't match the content-type header",
    )


@with_responses(FileFormatResponses)
async def validate_image_upload(upload: UploadFile) -> UploadFile:
    upload_header_data = await upload.read(FILE_HEADER_SIZE)
    image_type = match_image_filetype(upload_header_data)

    if image_type is None:
        raise FileFormatResponses.WRONG_FORMAT

    if image_type.mime != upload.content_type:
        raise FileFormatResponses.CONTENT_TYPE_MISMATCH

    await upload.seek(0)
    return upload


ValidatedImageUpload = Annotated[UploadFile, Depends(validate_image_upload)]


@with_responses(FileFormatResponses)
async def validate_document_upload(upload: UploadFile) -> UploadFile:
    upload_header_data = await upload.read(FILE_HEADER_SIZE)
    document_type = match_document_filetype(upload_header_data)

    if document_type is None:
        raise FileFormatResponses.WRONG_FORMAT

    if document_type.mime != upload.content_type:
        raise FileFormatResponses.CONTENT_TYPE_MISMATCH

    await upload.seek(0)
    return upload


ValidatedDocumentUpload = Annotated[UploadFile, Depends(validate_document_upload)]


@with_responses(FileFormatResponses)
async def validate_audio_upload(upload: UploadFile) -> UploadFile:
    upload_header_data = await upload.read(FILE_HEADER_SIZE)
    audio_type = match_audio_filetype(upload_header_data)

    if audio_type is None:
        raise FileFormatResponses.WRONG_FORMAT

    audio_extensions = guess_all_extensions(upload.content_type or "")

    if f".{audio_type.extension}" not in audio_extensions:
        raise FileFormatResponses.CONTENT_TYPE_MISMATCH

    await upload.seek(0)
    return upload


ValidatedAudioUpload = Annotated[UploadFile, Depends(validate_audio_upload)]


@with_responses(FileFormatResponses)
async def validate_presentation_upload(upload: UploadFile) -> UploadFile:
    upload_header_data = await upload.read(FILE_HEADER_SIZE)
    presentation_type = match_presentation_filetype(upload_header_data)

    if presentation_type is None:
        raise FileFormatResponses.WRONG_FORMAT

    if presentation_type.mime != upload.content_type:
        raise FileFormatResponses.CONTENT_TYPE_MISMATCH

    await upload.seek(0)
    return upload


ValidatedPresentationUpload = Annotated[
    UploadFile, Depends(validate_presentation_upload)
]

FILE_KIND_TO_FILETYPE_MATCHER: dict[
    FileKind, Callable[[bytes], filetype.Type | None]
] = {
    FileKind.IMAGE: match_image_filetype,
    FileKind.DOCUMENT: match_document_filetype,
    FileKind.AUDIO: match_audio_filetype,
    FileKind.PRESENTATION: match_presentation_filetype,
}


def detect_file_kind_and_filetype(
    upload_header_data: bytes,
) -> tuple[FileKind, filetype.Type | None]:
    for file_kind, filetype_matcher in FILE_KIND_TO_FILETYPE_MATCHER.items():
        detected_filetype = filetype_matcher(upload_header_data)
        if detected_filetype is not None:
            return file_kind, detected_filetype
    return FileKind.UNCATEGORIZED, None


class ContentTypeMismatchResponses(Responses):
    CONTENT_TYPE_MISMATCH = (
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "File content doesn't match the content-type header",
    )


@with_responses(ContentTypeMismatchResponses)
async def validate_and_categorize_upload(upload: UploadFile) -> FileKind:
    upload_header_data = await upload.read(FILE_HEADER_SIZE)
    await upload.seek(0)

    file_kind, detected_filetype = detect_file_kind_and_filetype(upload_header_data)
    if detected_filetype is None:
        return file_kind

    content_type_extensions = guess_all_extensions(upload.content_type or "")
    if (
        detected_filetype.mime != upload.content_type
        and f".{detected_filetype.extension}" not in content_type_extensions
    ):
        raise ContentTypeMismatchResponses.CONTENT_TYPE_MISMATCH

    return file_kind


UploadFileKind = Annotated[FileKind, Depends(validate_and_categorize_upload)]
