import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.utils.datetime import datetime_utc_now
from app.tutors.models.invitations_db import Invitation
from app.tutors.models.tutorships_db import Tutorship
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.factories import UserProfileFactory

pytestmark = pytest.mark.anyio


async def test_invitation_previewing(
    users_internal_respx_mock: MockRouter,
    student_client: TestClient,
    invitation: Invitation,
) -> None:
    tutor_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{invitation.tutor_id}/"
    ).respond(json=tutor_profile_data)

    assert_response(
        student_client.get(
            f"/api/protected/tutor-service/roles/student/invitations/{invitation.code}/preview/",
        ),
        expected_json={
            "tutor": {
                **tutor_profile_data,
                "user_id": invitation.tutor_id,
            },
        },
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


@freeze_time()
async def test_invitation_accepting(
    active_session: ActiveSession,
    student_user_id: int,
    student_client: TestClient,
    invitation: Invitation,
) -> None:
    initial_invitation_usage_count = invitation.usage_count

    assert_nodata_response(
        student_client.post(
            f"/api/protected/tutor-service/roles/student/invitations/{invitation.code}/usages/",
        )
    )

    async with active_session() as session:
        session.add(invitation)
        await session.refresh(invitation)
        assert invitation.usage_count == initial_invitation_usage_count + 1

        tutorship = await Tutorship.find_first_by_kwargs(
            tutor_id=invitation.tutor_id,
            student_id=student_user_id,
        )
        assert tutorship is not None
        assert_contains(
            tutorship,
            {
                "created_at": datetime_utc_now(),
                "active_classroom_count": 0,
            },
        )
        await tutorship.delete()


invitation_request_parametrization = pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param("GET", "preview/", id="preview"),
        pytest.param("POST", "usages/", id="accept"),
    ],
)


@invitation_request_parametrization
async def test_invitation_requesting_target_is_the_source(
    tutor_client: TestClient,
    invitation: Invitation,
    method: str,
    path: str,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=f"/api/protected/tutor-service/roles/student/invitations/{invitation.code}/{path}",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Target is the source"},
    )


@invitation_request_parametrization
async def test_invitation_not_finding(
    student_client: TestClient,
    deleted_invitation_code: str,
    method: str,
    path: str,
) -> None:
    assert_response(
        student_client.request(
            method=method,
            url=f"/api/protected/tutor-service/roles/student/invitations/{deleted_invitation_code}/{path}",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invitation not found"},
    )
