from typing import Annotated

from fastapi import Depends, UploadFile
from filetype import filetype  # type: ignore[import-untyped]
from filetype.types.image import Webp  # type: ignore[import-untyped]
from starlette import status

from app.common.fastapi_ext import Responses, with_responses


class FileFormatResponses(Responses):
    WRONG_FORMAT = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Invalid file format"


@with_responses(FileFormatResponses)
def validate_image_upload(upload: UploadFile) -> UploadFile:
    if not filetype.match(upload.file, [Webp()]):
        raise FileFormatResponses.WRONG_FORMAT
    return upload


ValidatedImageUpload = Annotated[UploadFile, Depends(validate_image_upload)]
