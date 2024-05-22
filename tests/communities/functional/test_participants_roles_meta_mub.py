import pytest
from starlette.testclient import TestClient

from app.communities.models.participants_db import Participant, ParticipantRole
from app.communities.models.roles_db import Role
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response

pytestmark = pytest.mark.anyio


async def test_role_assignment(
    mub_client: TestClient,
    active_session: ActiveSession,
    participant: Participant,
    role: Role,
) -> None:
    assert_nodata_response(
        mub_client.post(
            f"/mub/community-service/participants/{participant.id}/roles/{role.id}/",
        )
    )

    async with active_session():
        participant_role = await ParticipantRole.find_first_by_kwargs(
            participant_id=participant.id, role_id=role.id
        )
        assert participant_role is not None
        await participant_role.delete()


async def test_role_assignment_already_assigned(
    mub_client: TestClient,
    participant: Participant,
    role: Role,
    participant_role: ParticipantRole,
) -> None:
    assert_response(
        mub_client.post(
            f"/mub/community-service/participants/{participant.id}/roles/{role.id}/",
        ),
        expected_code=409,
        expected_json={"detail": "Role already assigned to the participant"},
    )


async def test_role_depriving(
    mub_client: TestClient,
    active_session: ActiveSession,
    participant: Participant,
    role: Role,
    participant_role: ParticipantRole,
) -> None:
    assert_nodata_response(
        mub_client.delete(
            f"/mub/community-service/participants/{participant.id}/roles/{role.id}/"
        )
    )

    async with active_session():
        assert (
            await ParticipantRole.find_first_by_kwargs(
                participant_id=participant.id, role_id=role.id
            )
        ) is None


async def test_role_depriving_not_assigned(
    mub_client: TestClient,
    participant: Participant,
    role: Role,
) -> None:
    assert_response(
        mub_client.delete(
            f"/mub/community-service/participants/{participant.id}/roles/{role.id}/",
        ),
        expected_code=404,
        expected_json={"detail": "Participant is not assigned this role"},
    )
