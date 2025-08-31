from collections.abc import Sequence

import pytest
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.tutorships_db import Tutorship
from app.common.config import settings
from tests.classrooms.conftest import TUTORSHIPS_LIST_SIZE
from tests.common.assert_contains_ext import assert_response
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values
from tests.factories import UserProfileFactory

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
    users_internal_respx_mock: MockRouter,
    student_client: TestClient,
    student_tutorships: Sequence[Tutorship],
    offset: int,
    limit: int,
) -> None:
    user_profiles: dict[int, AnyJSON] = {
        tutorship.tutor_id: UserProfileFactory.build_json()
        for tutorship in student_tutorships[offset:limit]
    }
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path="/users/",
        params={
            "user_ids": [
                tutorship.tutor_id for tutorship in student_tutorships[offset:limit]
            ]
        },
    ).respond(json=user_profiles)

    assert_response(
        student_client.get(
            "/api/protected/classroom-service/roles/student/tutors/",
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
            {
                "tutorship": Tutorship.StudentResponseSchema.model_validate(
                    tutorship, from_attributes=True
                ),
                "user": user_profiles[tutorship.tutor_id],
            }
            for tutorship in student_tutorships[offset:limit]
        ],
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_tutorship_retrieving(
    users_internal_respx_mock: MockRouter,
    student_client: TestClient,
    tutorship: Tutorship,
) -> None:
    tutor_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{tutorship.tutor_id}/"
    ).respond(json=tutor_profile_data)

    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student/tutors/{tutorship.tutor_id}/",
        ),
        expected_json=tutor_profile_data,
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
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
            url=f"/api/protected/classroom-service/roles/student/tutors/{tutor_user_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Tutorship not found"},
    )
