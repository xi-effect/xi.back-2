import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.tutors.models.classrooms_db import GroupClassroom
from app.tutors.models.invitations_db import GroupInvitation, IndividualInvitation
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_individual_invitations_listing(
    tutor_client: TestClient,
    individual_invitation_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/tutor-service/roles/tutor/individual-invitations/",
        ),
        expected_json=[individual_invitation_data],
    )


@freeze_time()
async def test_individual_invitation_creation(
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
) -> None:
    real_invitation_data: AnyJSON = assert_response(
        tutor_client.post(
            "/api/protected/tutor-service/roles/tutor/individual-invitations/"
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            "id": int,
            "code": str,
            "created_at": datetime_utc_now(),
            "usage_count": 0,
        },
    ).json()

    async with active_session():
        individual_invitation = await IndividualInvitation.find_first_by_id(
            real_invitation_data["id"]
        )
        assert individual_invitation is not None
        assert_contains(
            individual_invitation,
            {
                "code": real_invitation_data["code"],
                "tutor_id": tutor_user_id,
            },
        )
        await individual_invitation.delete()


async def test_invitation_creation_quantity_exceeded(
    active_session: ActiveSession,
    mock_stack: MockStack,
    tutor_user_id: int,
    tutor_client: TestClient,
) -> None:
    mock_stack.enter_mock(IndividualInvitation, "max_count_per_tutor", property_value=0)
    assert_response(
        tutor_client.post(
            "/api/protected/tutor-service/roles/tutor/individual-invitations/"
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Quantity exceeded"},
    )


@freeze_time()
async def test_group_invitation_creating_or_retrieving_new_invitation(
    active_session: ActiveSession,
    tutor_client: TestClient,
    group_classroom: GroupClassroom,
) -> None:
    real_invitation_data: AnyJSON = assert_response(
        tutor_client.post(
            "/api/protected/tutor-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/invitation/"
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            "id": int,
            "code": str,
            "created_at": datetime_utc_now(),
            "usage_count": 0,
        },
    ).json()

    async with active_session():
        group_invitation = await GroupInvitation.find_first_by_id(
            real_invitation_data["id"]
        )
        assert group_invitation is not None
        assert_contains(
            group_invitation,
            {
                "code": real_invitation_data["code"],
                "group_classroom_id": group_classroom.id,
            },
        )
        await group_invitation.delete()


async def test_group_invitation_creating_or_retrieving_invitation_exists(
    tutor_client: TestClient,
    group_classroom: GroupClassroom,
    group_invitation_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/tutor-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/invitation/"
        ),
        expected_json=group_invitation_data,
    )


async def test_group_invitation_creating_or_retrieving_classroom_not_found(
    tutor_client: TestClient,
    deleted_group_classroom_id: int,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/tutor-service/roles/tutor"
            f"/group-classrooms/{deleted_group_classroom_id}/invitation/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom not found"},
    )


async def test_invitation_deleting(
    tutor_client: TestClient,
    active_session: ActiveSession,
    individual_invitation: IndividualInvitation,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            f"/api/protected/tutor-service/roles/tutor"
            f"/individual-invitations/{individual_invitation.id}/"
        )
    )

    async with active_session():
        assert (
            await IndividualInvitation.find_first_by_id(individual_invitation.id)
        ) is None


async def test_invitation_deleting_invitation_access_denied(
    outsider_client: TestClient,
    individual_invitation: IndividualInvitation,
) -> None:
    assert_response(
        outsider_client.delete(
            f"/api/protected/tutor-service/roles/tutor"
            f"/individual-invitations/{individual_invitation.id}/"
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Invitation access denied"},
    )


async def test_invitation_deleting_invitation_not_found(
    outsider_client: TestClient,
    deleted_individual_invitation_id: int,
) -> None:
    assert_response(
        outsider_client.delete(
            f"/api/protected/tutor-service/roles/tutor"
            f"/individual-invitations/{deleted_individual_invitation_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invitation not found"},
    )
