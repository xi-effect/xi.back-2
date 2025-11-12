from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import (
    ClassroomKind,
    ClassroomStatus,
    GroupClassroom,
    IndividualClassroom,
)
from app.classrooms.models.enrollments_db import Enrollment
from app.classrooms.models.invitations_db import (
    GroupInvitation,
    IndividualInvitation,
    Invitation,
)
from app.classrooms.models.tutorships_db import Tutorship
from app.common.config import settings
from app.common.schemas.notifications_sch import (
    InvitationAcceptanceNotificationPayloadSchema,
    NotificationInputSchema,
    NotificationKind,
)
from app.common.schemas.users_sch import UserProfileSchema
from app.common.utils.datetime import datetime_utc_now
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.mock_stack import MockStack
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.factories import UserProfileFactory

pytestmark = pytest.mark.anyio


async def test_individual_invitation_previewing(
    users_internal_respx_mock: MockRouter,
    tutor_user_id: int,
    student_client: TestClient,
    individual_invitation: IndividualInvitation,
) -> None:
    tutor_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{tutor_user_id}/"
    ).respond(json=tutor_profile_data)

    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student"
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
    tutor_user_id: int,
    student_client: TestClient,
    individual_classroom: IndividualClassroom,
    individual_invitation: IndividualInvitation,
) -> None:
    tutor_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{tutor_user_id}/"
    ).respond(json=tutor_profile_data)

    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student"
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


@pytest.mark.parametrize(
    "existing_tutorship",
    [
        pytest.param(None, id="new_tutorship"),
        pytest.param(lf("tutorship"), id="old_tutorship"),
    ],
)
@freeze_time()
async def test_individual_invitation_accepting(
    active_session: ActiveSession,
    send_notification_mock: AsyncMock,
    users_internal_respx_mock: MockRouter,
    tutor_user_id: int,
    student_user_id: int,
    student_client: TestClient,
    individual_invitation: IndividualInvitation,
    existing_tutorship: Tutorship | None,
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
            f"/api/protected/classroom-service/roles/student"
            f"/invitations/{individual_invitation.code}/usages/",
        ),
        expected_json={
            "id": int,
            "kind": ClassroomKind.INDIVIDUAL,
            "status": ClassroomStatus.ACTIVE,
            "created_at": datetime_utc_now(),
            "tutor_id": tutor_user_id,
            "name": user_profiles[tutor_user_id].display_name,
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
                "created_at": (
                    datetime_utc_now()
                    if existing_tutorship is None
                    else existing_tutorship.created_at
                ),
                "active_classroom_count": (
                    1
                    if existing_tutorship is None
                    else existing_tutorship.active_classroom_count + 1
                ),
            },
        )
        await tutorship.delete()

        classroom = await IndividualClassroom.find_first_by_id(classroom_id)
        assert classroom is not None
        await classroom.delete()

    send_notification_mock.assert_awaited_once_with(
        NotificationInputSchema(
            payload=InvitationAcceptanceNotificationPayloadSchema(
                kind=NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1,
                invitation_id=individual_invitation.id,
                classroom_id=classroom_id,
                student_id=student_user_id,
            ),
            recipient_user_ids=[individual_invitation.tutor_id],
        )
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_individual_invitation_accepting_has_already_joined(
    student_client: TestClient,
    individual_classroom: IndividualClassroom,
    individual_invitation: IndividualInvitation,
) -> None:
    assert_response(
        student_client.post(
            f"/api/protected/classroom-service/roles/student"
            f"/invitations/{individual_invitation.code}/usages/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Already joined"},
    )


async def test_group_invitation_previewing(
    users_internal_respx_mock: MockRouter,
    tutor_user_id: int,
    student_client: TestClient,
    group_classroom_student_preview_data: AnyJSON,
    group_invitation: GroupInvitation,
) -> None:
    tutor_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{tutor_user_id}/"
    ).respond(json=tutor_profile_data)

    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student"
            f"/invitations/{group_invitation.code}/preview/",
        ),
        expected_json={
            "tutor": {
                **tutor_profile_data,
                "user_id": tutor_user_id,
            },
            "classroom": group_classroom_student_preview_data,
            "has_already_joined": False,
        },
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_group_invitation_previewing_has_already_joined(
    users_internal_respx_mock: MockRouter,
    tutor_user_id: int,
    student_client: TestClient,
    group_classroom_student_preview_data: AnyJSON,
    enrollment: Enrollment,
    group_invitation: GroupInvitation,
) -> None:
    tutor_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{tutor_user_id}/"
    ).respond(json=tutor_profile_data)

    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student"
            f"/invitations/{group_invitation.code}/preview/",
        ),
        expected_json={
            "tutor": {
                **tutor_profile_data,
                "user_id": tutor_user_id,
            },
            "classroom": group_classroom_student_preview_data,
            "has_already_joined": True,
        },
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


@pytest.mark.parametrize(
    "existing_tutorship",
    [
        pytest.param(None, id="new_tutorship"),
        pytest.param(lf("tutorship"), id="old_tutorship"),
    ],
)
@freeze_time()
async def test_group_invitation_accepting(
    active_session: ActiveSession,
    send_notification_mock: AsyncMock,
    tutor_user_id: int,
    student_user_id: int,
    student_client: TestClient,
    group_classroom: GroupClassroom,
    group_classroom_student_data: AnyJSON,
    group_invitation: GroupInvitation,
    existing_tutorship: Tutorship | None,
) -> None:
    initial_invitation_usage_count = group_invitation.usage_count

    assert_response(
        student_client.post(
            f"/api/protected/classroom-service/roles/student"
            f"/invitations/{group_invitation.code}/usages/",
        ),
        expected_json={
            **group_classroom_student_data,
            "enrollments_count": group_classroom.enrollments_count + 1,
        },
    )

    async with active_session() as session:
        session.add(group_invitation)
        await session.refresh(group_invitation)
        assert group_invitation.usage_count == initial_invitation_usage_count + 1

        tutorship = await Tutorship.find_first_by_kwargs(
            tutor_id=tutor_user_id,
            student_id=student_user_id,
        )
        assert tutorship is not None
        assert_contains(
            tutorship,
            {
                "created_at": (
                    datetime_utc_now()
                    if existing_tutorship is None
                    else existing_tutorship.created_at
                ),
                "active_classroom_count": (
                    1
                    if existing_tutorship is None
                    else existing_tutorship.active_classroom_count + 1
                ),
            },
        )
        await tutorship.delete()

        enrollment = await Enrollment.find_first_by_kwargs(
            group_classroom_id=group_invitation.group_classroom_id,
            student_id=student_user_id,
        )
        assert enrollment is not None
        await enrollment.delete()

    send_notification_mock.assert_awaited_once_with(
        NotificationInputSchema(
            payload=InvitationAcceptanceNotificationPayloadSchema(
                kind=NotificationKind.GROUP_INVITATION_ACCEPTED_V1,
                invitation_id=group_invitation.id,
                classroom_id=group_classroom.id,
                student_id=student_user_id,
            ),
            recipient_user_ids=[group_invitation.tutor_id],
        )
    )


async def test_group_invitation_accepting_enrollments_count_quantity_exceeded(
    mock_stack: MockStack,
    student_client: TestClient,
    group_invitation: GroupInvitation,
) -> None:
    mock_stack.enter_mock(
        GroupClassroom, "max_enrollments_count_per_group", property_value=0
    )

    assert_response(
        student_client.post(
            "/api/protected/classroom-service/roles/student"
            f"/invitations/{group_invitation.code}/usages/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Quantity exceeded"},
    )


async def test_group_invitation_accepting_has_already_joined(
    student_client: TestClient,
    group_invitation: IndividualInvitation,
    enrollment: Enrollment,
) -> None:
    assert_response(
        student_client.post(
            f"/api/protected/classroom-service/roles/student"
            f"/invitations/{group_invitation.code}/usages/",
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
    any_invitation: Invitation,
    method: str,
    path: str,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=(
                f"/api/protected/classroom-service/roles/student"
                f"/invitations/{any_invitation.code}/{path}"
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Target is the source"},
    )


@invitation_request_parametrization
async def test_invitation_not_finding(
    student_client: TestClient,
    invalid_invitation_code: str,
    method: str,
    path: str,
) -> None:
    assert_response(
        student_client.request(
            method=method,
            url=(
                f"/api/protected/classroom-service/roles/student/invitations"
                f"/{invalid_invitation_code}/{path}"
            ),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invitation not found"},
    )
