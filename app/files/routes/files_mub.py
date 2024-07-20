from pathlib import Path

from starlette.responses import FileResponse

from app.common.config import FILE_STORAGE_PATH_MUB
from app.common.fastapi_ext import APIRouterExt, Responses
from app.files.dependencies.validation_dep import ValidatedFile, ValidatedFiles
from app.files.models.files_db import File

router = APIRouterExt(tags=["files mub"])


class FileCreateResponses(Responses):
    FILENAME_ALREADY_IN_USE = 409, "Filename already in use"


@router.post(
    "/files/",
    summary="Upload files to the server",
    responses=FileCreateResponses.responses(),
    status_code=204,
)
async def upload_files(files: ValidatedFiles) -> None:
    for uploaded_file in files:
        if uploaded_file.filename in await File.get_all_files_names():
            raise FileCreateResponses.FILENAME_ALREADY_IN_USE
        with Path(FILE_STORAGE_PATH_MUB, str(uploaded_file.filename)).open("wb") as f:
            await File.create(filename=uploaded_file.filename)
            f.write(await uploaded_file.read())


class FileResponses(Responses):
    FILE_NOT_FOUND = 404, "File not found"


@router.get(
    "/files/{filename}",
    summary="Retrieve file by name",
    responses=FileResponses.responses(),
    response_class=FileResponse,
)
async def get_file(filename: str) -> FileResponse:
    file_path = Path(FILE_STORAGE_PATH_MUB) / filename
    file_db = await File.find_first_by_kwargs(filename=filename)
    if file_db is None or not file_path.exists():
        raise FileResponses.FILE_NOT_FOUND
    return FileResponse(
        path=file_path, media_type="application/octet-stream", filename=filename
    )


@router.put(
    "/files/{filename}",
    summary="Update file by name",
    responses=FileResponses.responses(),
    status_code=204,
)
async def update_file(filename: str, file: ValidatedFile) -> None:
    file_db = await File.find_first_by_kwargs(filename=filename)
    if file_db is None:
        raise FileResponses.FILE_NOT_FOUND
    Path(FILE_STORAGE_PATH_MUB, filename).unlink()
    with Path(FILE_STORAGE_PATH_MUB, str(file.filename)).open("wb") as f:
        f.write(await file.read())
    file_db.update(filename=file.filename)


@router.delete(
    "/files/{filename}",
    summary="Delete file by name",
    responses=FileResponses.responses(),
    status_code=204,
)
async def delete_file(filename: str) -> None:
    file_db = await File.find_first_by_kwargs(filename=filename)
    if file_db is None:
        raise FileResponses.FILE_NOT_FOUND
    await file_db.delete()
    Path(FILE_STORAGE_PATH_MUB, filename).unlink()
