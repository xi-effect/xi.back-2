from collections.abc import AsyncIterator
from os import stat
from uuid import UUID, uuid4

import pytest
from faker import Faker
from starlette.responses import FileResponse

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.storage.models.access_groups_db import AccessGroup
from app.storage.models.files_db import File, FileKind
from app.storage.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, PytestRequest
from tests.storage import factories


@pytest.fixture()
async def access_group_data() -> AnyJSON:
    return factories.AccessGroupInputFactory.build_json()


@pytest.fixture()
async def access_group(
    faker: Faker, active_session: ActiveSession, access_group_data: AnyJSON
) -> AccessGroup:
    async with active_session():
        return await AccessGroup.create(**access_group_data)


@pytest.fixture()
def missing_access_group_id() -> UUID:
    return uuid4()


@pytest.fixture()
async def ydoc(
    faker: Faker,
    active_session: ActiveSession,
    access_group: AccessGroup,
) -> YDoc:
    async with active_session():
        return await YDoc.create(
            access_group_id=access_group.id, content=faker.binary(length=64)
        )


@pytest.fixture()
def missing_ydoc_id() -> UUID:
    return uuid4()


@pytest.fixture()
def attachment(faker: Faker) -> bytes:
    return faker.bin_file(raw=True)  # type: ignore[no-any-return]


@pytest.fixture()
def image(faker: Faker) -> bytes:
    return faker.graphic_webp_file(raw=True)  # type: ignore[no-any-return]


@pytest.fixture(
    params=[
        pytest.param(member, id=member.value)
        for member in FileKind.__members__.values()
    ]
)
def file_kind(request: PytestRequest[FileKind]) -> FileKind:
    return request.param


@pytest.fixture()
def file_content(file_kind: FileKind, attachment: bytes, image: bytes) -> bytes:
    match file_kind:
        case FileKind.ATTACHMENT:
            return attachment
        case FileKind.IMAGE:
            return image


FILE_KIND_TO_CONTENT_TYPE: dict[FileKind, str] = {
    FileKind.ATTACHMENT: "application/x-tar",
    FileKind.IMAGE: "image/webp",
}


@pytest.fixture()
def file_content_type(file_kind: FileKind) -> str:
    return FILE_KIND_TO_CONTENT_TYPE[file_kind]


FILE_KIND_TO_EXTENSION: dict[FileKind, str] = {
    FileKind.ATTACHMENT: "tar",
    FileKind.IMAGE: "webp",
}


@pytest.fixture()
async def file(
    faker: Faker,
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    file_kind: FileKind,
    file_content: bytes,
) -> AsyncIterator[File]:
    async with active_session():
        file = await File.create(
            name=faker.file_name(extension=FILE_KIND_TO_EXTENSION[file_kind]),
            kind=file_kind,
            creator_user_id=proxy_auth_data.user_id,
        )

    with file.path.open("wb") as f:
        f.write(file_content)

    yield file

    async with active_session():
        file_for_deletion = await File.find_first_by_id(file.id)
        if file_for_deletion is not None:
            await file_for_deletion.delete()


@pytest.fixture()
def file_response(file: File) -> FileResponse:
    return FileResponse(file.path, stat_result=stat(file.path))


@pytest.fixture()
def file_etag(file_response: FileResponse) -> str | None:
    return file_response.headers["etag"]


@pytest.fixture()
def file_last_modified(file_response: FileResponse) -> str | None:
    return file_response.headers["last-modified"]


@pytest.fixture()
def missing_file_id() -> UUID:
    return uuid4()
