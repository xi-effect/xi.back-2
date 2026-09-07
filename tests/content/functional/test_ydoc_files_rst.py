from uuid import UUID

import pytest
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.config import content_token_provider
from app.common.schemas.content_sch import ContentTokenPayloadSchema
from app.content.models.files_db import File
from app.content.models.ydoc_files_db import YDocFile
from app.content.models.ydocs_db import YDoc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.content import factories
from tests.content.conftest import ContentTokenGeneratorProtocol

pytestmark = pytest.mark.anyio


@pytest.fixture()
def library_file_addition_content_token(
    material_id: UUID,
    tutor_user_id: int,
    ydoc: YDoc,
) -> str:
    content_token_payload: ContentTokenPayloadSchema = (
        factories.ContentTokenPayloadFactory.build(
            material_id=material_id,
            ydoc_id=ydoc.id,
            user_id=tutor_user_id,
            can_add_library_files=True,
        )
    )
    return content_token_provider.serialize_and_sign(content_token_payload)


async def test_adding_library_file_to_ydoc(
    active_session: ActiveSession,
    tutor_client: TestClient,
    ydoc: YDoc,
    file: File,
    library_file_addition_content_token: str,
) -> None:
    assert_nodata_response(
        tutor_client.put(
            f"/api/protected/content-service/ydocs/{ydoc.id}/files/{file.id}/",
            headers={"X-Content-Token": library_file_addition_content_token},
        )
    )

    async with active_session():
        assert (
            await YDocFile.find_first_by_ids(ydoc_id=ydoc.id, file_id=file.id)
            is not None
        )


async def test_adding_library_file_to_ydoc_ydoc_file_already_exists(
    active_session: ActiveSession,
    tutor_client: TestClient,
    ydoc_file: YDocFile,
    library_file_addition_content_token: str,
) -> None:
    assert_nodata_response(
        tutor_client.put(
            "/api/protected/content-service"
            f"/ydocs/{ydoc_file.ydoc_id}/files/{ydoc_file.file_id}/",
            headers={"X-Content-Token": library_file_addition_content_token},
        )
    )

    async with active_session():
        assert (
            await YDocFile.find_first_by_ids(
                ydoc_id=ydoc_file.ydoc_id,
                file_id=ydoc_file.file_id,
            )
            is not None
        )


async def test_adding_library_file_to_ydoc_insufficient_permissions(
    content_token_generator: ContentTokenGeneratorProtocol,
    material_id: UUID,
    tutor_user_id: int,
    tutor_client: TestClient,
    ydoc: YDoc,
    file: File,
) -> None:
    content_token = content_token_generator(
        material_id,
        ydoc.id,
        tutor_user_id,
        can_add_library_files=False,
    )

    assert_response(
        tutor_client.put(
            f"/api/protected/content-service/ydocs/{ydoc.id}/files/{file.id}/",
            headers={"X-Content-Token": content_token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Insufficient content token permissions"},
    )


@pytest.mark.parametrize(
    "content_token",
    [
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("ydoc.id"),
                lf("outsider_user_id"),
                can_add_library_files=True,
            ),
            id="incorrect_user",
        ),
        pytest.param(
            lfc(
                "content_token_generator",
                lf("material_id"),
                lf("other_ydoc.id"),
                lf("tutor_user_id"),
                can_add_library_files=True,
            ),
            id="wrong_ydoc",
        ),
        pytest.param(
            lfc("faker.password"),
            id="malformed_token",
        ),
    ],
)
async def test_adding_library_file_to_ydoc_invalid_token(
    tutor_client: TestClient,
    ydoc: YDoc,
    file: File,
    content_token: str,
) -> None:
    assert_response(
        tutor_client.put(
            f"/api/protected/content-service/ydocs/{ydoc.id}/files/{file.id}/",
            headers={"X-Content-Token": content_token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invalid content token"},
    )


async def test_adding_library_file_to_ydoc_file_access_denied(
    content_token_generator: ContentTokenGeneratorProtocol,
    material_id: UUID,
    outsider_user_id: int,
    outsider_client: TestClient,
    ydoc: YDoc,
    file: File,
) -> None:
    content_token = content_token_generator(
        material_id,
        ydoc.id,
        outsider_user_id,
        can_add_library_files=True,
    )

    assert_response(
        outsider_client.put(
            f"/api/protected/content-service/ydocs/{ydoc.id}/files/{file.id}/",
            headers={"X-Content-Token": content_token},
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "File access denied"},
    )


async def test_adding_library_file_to_ydoc_ydoc_not_found(
    content_token_generator: ContentTokenGeneratorProtocol,
    material_id: UUID,
    tutor_user_id: int,
    tutor_client: TestClient,
    missing_ydoc_id: UUID,
    file: File,
) -> None:
    content_token = content_token_generator(
        material_id,
        missing_ydoc_id,
        tutor_user_id,
        can_add_library_files=True,
    )

    assert_response(
        tutor_client.put(
            "/api/protected/content-service"
            f"/ydocs/{missing_ydoc_id}/files/{file.id}/",
            headers={"X-Content-Token": content_token},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "YDoc not found"},
    )


async def test_adding_library_file_to_ydoc_file_not_found(
    tutor_client: TestClient,
    ydoc: YDoc,
    missing_file_id: UUID,
    library_file_addition_content_token: str,
) -> None:
    assert_response(
        tutor_client.put(
            "/api/protected/content-service"
            f"/ydocs/{ydoc.id}/files/{missing_file_id}/",
            headers={"X-Content-Token": library_file_addition_content_token},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "File not found"},
    )
