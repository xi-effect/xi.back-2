from mimetypes import guess_all_extensions
from typing import Annotated

from fastapi import Depends, UploadFile
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.common.filetype_ext import (
    FILE_HEADER_SIZE,
    match_audio_filetype,
    match_document_filetype,
    match_image_filetype,
)


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
