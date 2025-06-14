from typing import Any

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.tutors.models.subjects_db import Subject
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.tutors import factories

pytestmark = pytest.mark.anyio


async def test_subject_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
) -> None:
    subject_input_data = factories.SubjectInputMUBFactory.build_json()
    subject_id: int = assert_response(
        mub_client.post(
            "/mub/tutor-service/subjects/",
            json=subject_input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **subject_input_data,
            "id": int,
        },
    ).json()["id"]

    async with active_session():
        subject = await Subject.find_first_by_id(subject_id)
        assert subject is not None
        await subject.delete()


async def test_subject_creation_subject_already_exists(
    active_session: ActiveSession,
    mub_client: TestClient,
    subject_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.post(
            "/mub/tutor-service/subjects/",
            json=subject_data,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Subject already exists"},
    )


async def test_subject_updating(
    mub_client: TestClient,
    subject_data: AnyJSON,
) -> None:
    patch_subject_data = factories.SubjectPatchMUBFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/tutor-service/subjects/{subject_data["id"]}/",
            json=patch_subject_data,
        ),
        expected_json={
            **subject_data,
            **patch_subject_data,
        },
    )


async def test_subject_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    subject: Subject,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/tutor-service/subjects/{subject.id}/")
    )

    async with active_session():
        assert await Subject.find_first_by_id(subject.id) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("PATCH", factories.SubjectPatchMUBFactory, id="update"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_subject_not_finding(
    mub_client: TestClient,
    deleted_subject_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method=method,
            url=f"/mub/tutor-service/subjects/{deleted_subject_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Subject not found"},
    )
