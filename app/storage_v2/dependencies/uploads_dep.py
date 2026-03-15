from typing import Annotated

from fastapi import Depends, UploadFile
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.common.filetype_ext import FILE_HEADER_SIZE, match_image_filetype


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
