from typing import Annotated

from fastapi import Depends, UploadFile

from app.common.config import ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE
from app.common.fastapi_ext import Responses, with_responses


class FileValidationResponses(Responses):
    FILE_EXTENSION_NOT_SUPPORTED = 415, "File extension not supported"
    FILE_SIZE_TOO_LARGE = 413, "File size is too large"


@with_responses(FileValidationResponses)
def validate_files(files: list[UploadFile]) -> list[UploadFile]:
    for uploaded_file in files:
        if str(uploaded_file.filename).split(".")[-1] not in ALLOWED_FILE_EXTENSIONS:
            raise FileValidationResponses.FILE_EXTENSION_NOT_SUPPORTED
        if uploaded_file.size is not None and uploaded_file.size > MAX_FILE_SIZE:
            raise FileValidationResponses.FILE_SIZE_TOO_LARGE
    return files


ValidatedFiles = Annotated[list[UploadFile], Depends(validate_files)]


@with_responses(FileValidationResponses)
def validate_file(single_file: UploadFile) -> UploadFile:
    if str(single_file.filename).split(".")[-1] not in ALLOWED_FILE_EXTENSIONS:
        raise FileValidationResponses.FILE_EXTENSION_NOT_SUPPORTED
    if single_file.size is not None and single_file.size > MAX_FILE_SIZE:
        raise FileValidationResponses.FILE_SIZE_TOO_LARGE
    return single_file


ValidatedFile = Annotated[UploadFile, Depends(validate_file)]
