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
    participant_role_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/participants/{participant.id}/roles/{role.id}/",
        ),
        expected_code=201,
        expected_json={
            "id": int,
            "role_id": role.id,
        },
    ).json()["id"]

    async with active_session():
        participant_role = await ParticipantRole.find_first_by_id(participant_role_id)
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
        expected_json={"detail": "Participant is already have this role"},
    )


async def test_role_removing(
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
        assert (await ParticipantRole.find_first_by_id(participant_role.id)) is None


async def test_role_removing_already_removed(
    mub_client: TestClient,
    participant: Participant,
    role: Role,
) -> None:
    assert_response(
        mub_client.delete(
            f"/mub/community-service/participants/{participant.id}/roles/{role.id}/",
        ),
        expected_code=409,
        expected_json={"detail": "Participant does not have this role"},
    )
