from dataclasses import dataclass
from os import stat
from typing import Any, Protocol
from uuid import UUID, uuid4

import pytest
from faker import Faker
from pytest_lazy_fixtures import lf
from starlette.responses import FileResponse
from starlette.testclient import TestClient

from app.common.config import settings, storage_token_provider
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.storage_v2.models.access_groups_db import AccessGroup, AccessGroupFile
from app.storage_v2.models.files_db import File, FileKind
from app.storage_v2.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, PytestRequest
from tests.factories import ProxyAuthDataFactory
from tests.storage_v2 import factories


class StorageTokenGeneratorProtocol(Protocol):
    def __call__(
        self,
        access_group_id: UUID,
        user_id: int,
        **overrides: Any,
    ) -> str:
        pass


@pytest.fixture(scope="session")
def storage_token_generator() -> StorageTokenGeneratorProtocol:
    def storage_token_generator_inner(
        access_group_id: UUID,
        user_id: int,
        **overrides: Any,
    ) -> str:
        return storage_token_provider.serialize_and_sign(
            factories.StorageTokenPayloadFactory.build(
                access_group_id=access_group_id,
                user_id=user_id,
                **overrides,
            )
        )

    return storage_token_generator_inner


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_user_id(outsider_auth_data: ProxyAuthData) -> int:
    return outsider_auth_data.user_id


@pytest.fixture()
def outsider_internal_client(
    client: TestClient, outsider_auth_data: ProxyAuthData
) -> TestClient:
    return TestClient(
        client.app,
        headers={
            **outsider_auth_data.as_headers,
            "X-Api-Key": settings.api_key,
        },
    )


@pytest.fixture()
async def ydoc(faker: Faker, active_session: ActiveSession) -> YDoc:
    async with active_session():
        return await YDoc.create(content=faker.binary(length=64))


@pytest.fixture()
async def other_ydoc(faker: Faker, active_session: ActiveSession) -> YDoc:
    async with active_session():
        return await YDoc.create(content=faker.binary(length=64))


@pytest.fixture()
def missing_ydoc_id() -> UUID:
    return uuid4()


@pytest.fixture()
async def access_group(active_session: ActiveSession, ydoc: YDoc) -> AccessGroup:
    async with active_session():
        return await AccessGroup.create(main_ydoc_id=ydoc.id)


@pytest.fixture()
def missing_access_group_id() -> UUID:
    return uuid4()


@pytest.fixture()
def uncategorized_file_content(faker: Faker) -> bytes:
    return faker.bin_file(raw=True)  # type: ignore[no-any-return]


@pytest.fixture()
def image_file_content(faker: Faker) -> bytes:
    return faker.graphic_webp_file(raw=True)  # type: ignore[no-any-return]


@dataclass
class FileInputData:
    kind: FileKind
    name: str
    content: bytes
    content_type: str


@pytest.fixture()
def uncategorized_file_input_data(
    faker: Faker, uncategorized_file_content: bytes
) -> FileInputData:
    return FileInputData(
        kind=FileKind.UNCATEGORIZED,
        name=faker.file_name(),
        content=uncategorized_file_content,
        content_type=faker.mime_type(),
    )


@pytest.fixture()
def image_file_input_data(faker: Faker, image_file_content: bytes) -> FileInputData:
    return FileInputData(
        kind=FileKind.IMAGE,
        name=faker.file_name(extension="webp"),
        content=image_file_content,
        content_type="image/webp",
    )


@pytest.fixture(
    params=[
        pytest.param(lf("uncategorized_file_input_data"), id="uncategorized"),
        pytest.param(lf("image_file_input_data"), id="image"),
    ],
)
def parametrized_file_input_data(
    request: PytestRequest[FileInputData],
) -> FileInputData:
    return request.param


@pytest.fixture()
async def file(
    active_session: ActiveSession,
    parametrized_file_input_data: FileInputData,
) -> File:
    async with active_session():
        file = await File.create(
            name=parametrized_file_input_data.name,
            kind=parametrized_file_input_data.kind,
        )

    with file.path.open("wb") as f:
        f.write(parametrized_file_input_data.content)

    return file


@pytest.fixture()
def file_data(file: File) -> AnyJSON:
    return File.ResponseSchema.model_validate(file, from_attributes=True).model_dump(
        mode="json"
    )


@pytest.fixture()
async def access_group_file(
    active_session: ActiveSession,
    access_group: AccessGroup,
    file: File,
) -> AccessGroupFile:
    async with active_session():
        return await AccessGroupFile.create(
            access_group_id=access_group.id,
            file_id=file.id,
        )


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
