from datetime import datetime
from io import BytesIO
from os import stat
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, Header, UploadFile
from PIL import Image
from pydantic import BeforeValidator
from starlette import status
from starlette.responses import FileResponse, Response
from starlette.staticfiles import NotModifiedResponse

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.filetype_ext import PRESENTATION_CONTENT_TYPE
from app.content.dependencies.content_token_dep import (
    ensure_content_token_allows_reading_files,
    ensure_content_token_allows_uploading_files,
)
from app.content.dependencies.files_dep import MyFileByID
from app.content.dependencies.uploads_dep import (
    ValidatedAudioUpload,
    ValidatedDocumentUpload,
    ValidatedImageUpload,
    ValidatedPresentationUpload,
)
from app.content.dependencies.ydocs_dep import ContentTokenYDoc
from app.content.models.files_db import File, FileKind
from app.content.models.ydoc_files_db import YDocFile
from app.content.models.ydocs_db import YDoc

router = APIRouterExt(tags=["files"])


async def upload_file(
    ydoc: YDoc,
    auth_data: AuthorizationData,
    upload_content: bytes,
    upload_filename: str | None,
    file_kind: FileKind,
    content_type: str,
) -> File:
    filename = Path(upload_filename or "upload")

    file = await File.create_with_content(
        content=upload_content,
        owner_id=ydoc.owner_id,
        uploader_id=auth_data.user_id,
        name=filename.stem,
        extension=filename.suffix.lstrip("."),
        file_kind=file_kind,
        content_type=content_type,
    )

    await YDocFile.create(
        ydoc_id=ydoc.id,
        file_id=file.id,
    )

    return file


DEFAULT_CONTENT_TYPE = "application/octet-stream"


@router.post(
    "/file-kinds/uncategorized/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.ResponseSchema,
    summary="Upload a new uncategorized file",
    dependencies=[Depends(ensure_content_token_allows_uploading_files)],
)
async def upload_uncategorized_file(
    ydoc: ContentTokenYDoc,
    auth_data: AuthorizationData,
    upload: UploadFile,
) -> File:
    return await upload_file(
        ydoc=ydoc,
        auth_data=auth_data,
        upload_content=await upload.read(),
        upload_filename=upload.filename,
        file_kind=FileKind.UNCATEGORIZED,
        content_type=upload.content_type or DEFAULT_CONTENT_TYPE,
    )


@router.post(
    "/file-kinds/image/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.ResponseSchema,
    summary="Upload a new image file",
    dependencies=[Depends(ensure_content_token_allows_uploading_files)],
)
async def upload_image_file(
    ydoc: ContentTokenYDoc,
    auth_data: AuthorizationData,
    upload: ValidatedImageUpload,
) -> File:
    image = Image.open(BytesIO(await upload.read()))
    processed_image = BytesIO()
    image.save(processed_image, format="webp")
    processed_image.seek(0)

    return await upload_file(
        ydoc=ydoc,
        auth_data=auth_data,
        upload_content=processed_image.read(),
        upload_filename=upload.filename,
        file_kind=FileKind.IMAGE,
        content_type="image/webp",
    )


@router.post(
    "/file-kinds/document/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.ResponseSchema,
    summary="Upload a new document file",
    dependencies=[Depends(ensure_content_token_allows_uploading_files)],
)
async def upload_document_file(
    ydoc: ContentTokenYDoc,
    auth_data: AuthorizationData,
    upload: ValidatedDocumentUpload,
) -> File:
    return await upload_file(
        ydoc=ydoc,
        auth_data=auth_data,
        upload_content=await upload.read(),
        upload_filename=upload.filename,
        file_kind=FileKind.DOCUMENT,
        content_type="application/pdf",
    )


@router.post(
    "/file-kinds/audio/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.ResponseSchema,
    summary="Upload a new audio file",
    dependencies=[Depends(ensure_content_token_allows_uploading_files)],
)
async def upload_audio_file(
    ydoc: ContentTokenYDoc,
    auth_data: AuthorizationData,
    upload: ValidatedAudioUpload,
) -> File:
    return await upload_file(
        ydoc=ydoc,
        auth_data=auth_data,
        upload_content=await upload.read(),
        upload_filename=upload.filename,
        file_kind=FileKind.AUDIO,
        content_type=upload.content_type or DEFAULT_CONTENT_TYPE,
    )


@router.post(
    "/file-kinds/presentation/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.ResponseSchema,
    summary="Upload a new presentation file",
    dependencies=[Depends(ensure_content_token_allows_uploading_files)],
)
async def upload_presentation_file(
    ydoc: ContentTokenYDoc,
    auth_data: AuthorizationData,
    upload: ValidatedPresentationUpload,
) -> File:
    return await upload_file(
        ydoc=ydoc,
        auth_data=auth_data,
        upload_content=await upload.read(),
        upload_filename=upload.filename,
        file_kind=FileKind.PRESENTATION,
        content_type=PRESENTATION_CONTENT_TYPE,
    )


@router.get(
    "/files/{file_id}/meta/",
    response_model=File.ResponseSchema,
    summary="Read meta of any file by id",
    dependencies=[Depends(ensure_content_token_allows_reading_files)],
)
async def retrieve_file_meta(file: MyFileByID) -> File:
    return file


def parse_http_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S GMT")


def parse_http_datetime_header(value: Any) -> Any:
    return parse_http_datetime(value) if isinstance(value, str) else value


@router.get(
    "/files/{file_id}/",
    response_model=File.ResponseSchema,
    summary="Read any file by id",
    dependencies=[Depends(ensure_content_token_allows_reading_files)],
)
async def read_file(
    file: MyFileByID,
    if_none_match: Annotated[str, Header()] = "",
    if_modified_since: Annotated[
        datetime | None,
        BeforeValidator(parse_http_datetime_header),
        Header(),
    ] = None,
) -> Response:
    response = FileResponse(
        path=file.path,
        filename=file.filename,
        media_type=file.content_type,
        content_disposition_type=file.content_disposition,
        stat_result=stat(file.path),
    )

    etag = response.headers.get("etag")
    if etag in {tag.strip(" W/") for tag in if_none_match.split(",")}:
        return NotModifiedResponse(headers=response.headers)

    last_modified = parse_http_datetime(response.headers["last-modified"])
    if if_modified_since is not None and if_modified_since >= last_modified:
        return NotModifiedResponse(headers=response.headers)

    return response
