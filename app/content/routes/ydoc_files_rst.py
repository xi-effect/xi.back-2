from fastapi import Depends
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.content.dependencies.content_token_dep import (
    ensure_content_token_allows_adding_library_files,
)
from app.content.dependencies.files_dep import MyLibraryFileByID
from app.content.dependencies.ydocs_dep import MyYDocByID
from app.content.models.ydoc_files_db import YDocFile

router = APIRouterExt(tags=["ydoc files"])


@router.put(
    path="/ydocs/{ydoc_id}/files/{file_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add a library file to a ydoc by ids",
    dependencies=[Depends(ensure_content_token_allows_adding_library_files)],
)
async def add_library_file_to_ydoc(
    ydoc: MyYDocByID,
    file: MyLibraryFileByID,
) -> None:
    await YDocFile.upsert_by_ids(ydoc_id=ydoc.id, file_id=file.id)
