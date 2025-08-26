import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.schemas.users_sch import UserProfileSchema
from app.common.utils.datetime import datetime_utc_now
from app.tutors.models.classrooms_db import (
    ClassroomKind,
    ClassroomStatus,
    IndividualClassroom,
)
from app.tutors.models.invitations_db import IndividualInvitation
from app.tutors.models.tutorships_db import Tutorship
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.factories import UserProfileFactory

pytestmark = pytest.mark.anyio


async def test_individual_invitation_previewing(
    users_internal_respx_mock: MockRouter,
    student_client: TestClient,
    tutor_user_id: int,
    individual_invitation: IndividualInvitation,
) -> None:
    tutor_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{individual_invitation.tutor_id}/"
    ).respond(json=tutor_profile_data)

    assert_response(
        student_client.get(
            f"/api/protected/tutor-service/roles/student"
            f"/invitations/{individual_invitation.code}/preview/",
        ),
        expected_json={
            "tutor": {
                **tutor_profile_data,
                "user_id": tutor_user_id,
            },
            "existing_classroom_id": None,
        },
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_individual_invitation_previewing_has_already_joined(
    users_internal_respx_mock: MockRouter,
    student_client: TestClient,
    tutor_user_id: int,
    individual_invitation: IndividualInvitation,
    individual_classroom: IndividualClassroom,
) -> None:
    tutor_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{individual_invitation.tutor_id}/"
    ).respond(json=tutor_profile_data)

    assert_response(
        student_client.get(
            f"/api/protected/tutor-service/roles/student"
            f"/invitations/{individual_invitation.code}/preview/",
        ),
        expected_json={
            "tutor": {
                **tutor_profile_data,
                "user_id": tutor_user_id,
            },
            "existing_classroom_id": individual_classroom.id,
        },
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


@freeze_time()
async def test_individual_invitation_accepting(
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    student_client: TestClient,
    tutor_user_id: int,
    student_user_id: int,
    individual_invitation: IndividualInvitation,
) -> None:
    user_profiles: dict[int, UserProfileSchema] = {
        tutor_user_id: UserProfileFactory.build(),
        student_user_id: UserProfileFactory.build(),
    }
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path="/users/",
        params={"user_ids": [tutor_user_id, student_user_id]},
    ).respond(
        json={
            user_id: user_profile.model_dump(mode="json")
            for user_id, user_profile in user_profiles.items()
        }
    )

    initial_invitation_usage_count = individual_invitation.usage_count

    classroom_id = assert_response(
        student_client.post(
            f"/api/protected/tutor-service/roles/student"
            f"/invitations/{individual_invitation.code}/usages/",
        ),
        expected_json={
            "id": int,
            "kind": ClassroomKind.INDIVIDUAL,
            "status": ClassroomStatus.ACTIVE,
            "created_at": datetime_utc_now(),
            "tutor_id": tutor_user_id,
            "name": (
                user_profiles[tutor_user_id].display_name
                or user_profiles[tutor_user_id].username
            ),
            "description": None,
        },
    ).json()["id"]

    async with active_session() as session:
        session.add(individual_invitation)
        await session.refresh(individual_invitation)
        assert individual_invitation.usage_count == initial_invitation_usage_count + 1

        tutorship = await Tutorship.find_first_by_kwargs(
            tutor_id=tutor_user_id,
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

        classroom = await IndividualClassroom.find_first_by_id(classroom_id)
        assert classroom is not None
        await classroom.delete()

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_individual_invitation_accepting_has_already_joined(
    student_client: TestClient,
    individual_invitation: IndividualInvitation,
    individual_classroom: IndividualClassroom,
) -> None:
    assert_response(
        student_client.post(
            f"/api/protected/tutor-service/roles/student"
            f"/invitations/{individual_invitation.code}/usages/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Already joined"},
    )


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
    individual_invitation: IndividualInvitation,  # TODO nq any_invitation
    method: str,
    path: str,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=(
                f"/api/protected/tutor-service/roles/student"
                f"/invitations/{individual_invitation.code}/{path}"
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Target is the source"},
    )


@invitation_request_parametrization
async def test_invitation_not_finding(
    student_client: TestClient,
    deleted_individual_invitation_code: str,  # TODO nq any_invitation
    method: str,
    path: str,
) -> None:
    assert_response(
        student_client.request(
            method=method,
            url=(
                f"/api/protected/tutor-service/roles/student/invitations"
                f"/{deleted_individual_invitation_code}/{path}"
            ),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invitation not found"},
    )
