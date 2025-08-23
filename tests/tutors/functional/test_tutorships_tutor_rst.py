from collections.abc import Sequence

import pytest
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.tutors.models.tutorships_db import Tutorship
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values
from tests.factories import UserProfileFactory
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
    users_internal_respx_mock: MockRouter,
    tutor_client: TestClient,
    tutor_tutorships: Sequence[Tutorship],
    offset: int,
    limit: int,
) -> None:
    user_profiles: dict[str, AnyJSON] = {
        str(tutorship.student_id): UserProfileFactory.build_json()
        for tutorship in tutor_tutorships[offset:limit]
    }
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path="/users/",
        params={
            "user_ids": [
                tutorship.student_id for tutorship in tutor_tutorships[offset:limit]
            ]
        },
    ).respond(json=user_profiles)

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
            {
                "tutorship": Tutorship.TutorResponseSchema.model_validate(
                    tutorship, from_attributes=True
                ),
                "user": user_profiles[str(tutorship.student_id)],
            }
            for tutorship in tutor_tutorships[offset:limit]
        ],
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_tutorship_retrieving(
    users_internal_respx_mock: MockRouter,
    tutor_client: TestClient,
    tutorship: Tutorship,
) -> None:
    student_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{tutorship.student_id}/"
    ).respond(json=student_profile_data)

    assert_response(
        tutor_client.get(
            f"/api/protected/tutor-service/roles/tutor/students/{tutorship.student_id}/",
        ),
        expected_json=student_profile_data,
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
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
