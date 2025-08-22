from collections.abc import Sequence

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.tutors.models.tutorships_db import Tutorship
from tests.common.assert_contains_ext import assert_response
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
    student_client: TestClient,
    student_tutorships: Sequence[Tutorship],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/tutor-service/roles/student/tutors/",
            params=remove_none_values(
                {
                    "created_before": (
                        None
                        if offset == 0
                        else student_tutorships[offset - 1].created_at.isoformat()
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=[
            Tutorship.StudentResponseSchema.model_validate(
                tutorship, from_attributes=True
            )
            for tutorship in student_tutorships
        ][offset:limit],
    )


async def test_tutorship_retrieving(
    student_client: TestClient,
    tutorship: Tutorship,
    tutorship_data: AnyJSON,
) -> None:
    assert_response(
        student_client.get(
            f"/api/protected/tutor-service/roles/student/tutors/{tutorship.tutor_id}/",
        ),
        expected_json=tutorship_data,
    )


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("GET", id="retrieve"),
    ],
)
async def test_tutorship_not_finding(
    student_client: TestClient,
    tutor_user_id: int,
    method: str,
) -> None:
    assert_response(
        student_client.request(
            method=method,
            url=f"/api/protected/tutor-service/roles/student/tutors/{tutor_user_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Tutorship not found"},
    )
