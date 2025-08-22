from collections.abc import Sequence

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.tutors.models.tutorships_db import Tutorship
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values
from tests.tutors.conftest import TUTORSHIPS_LIST_SIZE

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, TUTORSHIPS_LIST_SIZE, id="start_to_end"),
        pytest.param(0, TUTORSHIPS_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            TUTORSHIPS_LIST_SIZE // 2, TUTORSHIPS_LIST_SIZE, id="middle_to_end"
        ),
    ],
)
async def test_tutorships_listing(
    tutor_client: TestClient,
    tutor_tutorships: Sequence[Tutorship],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/tutor-service/roles/tutor/students/",
            params=remove_none_values(
                {
                    "created_before": (
                        None
                        if offset == 0
                        else tutor_tutorships[offset - 1].created_at.isoformat()
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=[
            Tutorship.TutorResponseSchema.model_validate(
                tutorship, from_attributes=True
            )
            for tutorship in tutor_tutorships
        ][offset:limit],
    )


async def test_tutorship_retrieving(
    tutor_client: TestClient,
    tutorship: Tutorship,
    tutorship_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            f"/api/protected/tutor-service/roles/tutor/students/{tutorship.student_id}/",
        ),
        expected_json=tutorship_data,
    )


async def test_tutorship_deleting(
    active_session: ActiveSession,
    tutor_client: TestClient,
    tutorship: Tutorship,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            f"/api/protected/tutor-service/roles/tutor/students/{tutorship.student_id}/",
        )
    )

    async with active_session():
        assert (
            await Tutorship.find_first_by_kwargs(
                tutor_id=tutorship.tutor_id,
                student_id=tutorship.student_id,
            )
            is None
        )


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("GET", id="retrieve"),
        pytest.param("DELETE", id="delete"),
    ],
)
async def test_tutorship_not_finding(
    tutor_client: TestClient,
    student_user_id: int,
    method: str,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=f"/api/protected/tutor-service/roles/tutor/students/{student_user_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Tutorship not found"},
    )
