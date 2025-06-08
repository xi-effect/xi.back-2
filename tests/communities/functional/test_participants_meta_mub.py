from typing import Any

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.communities.factories import ParticipantMUBPatchFactory

pytestmark = pytest.mark.anyio


async def test_participants_listing(
    mub_client: TestClient,
    community: Community,
    participants_data: list[AnyJSON],
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/communities/{community.id}/participants/",
        ),
        expected_json=participants_data,
    )


async def test_participants_listing_empty_list(
    mub_client: TestClient,
    community: Community,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/communities/{community.id}/participants/",
        ),
        expected_json=[],
    )


async def test_participants_listing_community_not_found(
    mub_client: TestClient,
    deleted_community_id: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/communities/{deleted_community_id}/participants/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Community not found"},
    )


@pytest.fixture()
def participant_patch_data() -> AnyJSON:
    return ParticipantMUBPatchFactory.build_json()


async def test_participant_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
    participant_user_id: int,
    participant_patch_data: AnyJSON,
) -> None:
    participant_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/participants/",
            params={"user_id": participant_user_id},
            json=participant_patch_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **participant_patch_data,
            "user_id": participant_user_id,
            "id": int,
        },
    ).json()["id"]

    async with active_session():
        participant = await Participant.find_first_by_id(participant_id)
        assert participant is not None
        await participant.delete()


async def test_participant_retrieving(
    mub_client: TestClient,
    participant: Participant,
    participant_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/participants/{participant.id}/"),
        expected_json=participant_data,
    )


async def test_participant_updating(
    mub_client: TestClient,
    participant: Participant,
    participant_data: AnyJSON,
    participant_patch_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.patch(
            f"/mub/community-service/participants/{participant.id}/",
            json=participant_patch_data,
        ),
        expected_json={**participant_data, **participant_patch_data},
    )


async def test_participant_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    participant: Participant,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/participants/{participant.id}/")
    )

    async with active_session():
        assert (await Participant.find_first_by_id(participant.id)) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", ParticipantMUBPatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_participant_not_finding(
    mub_client: TestClient,
    active_session: ActiveSession,
    deleted_participant_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/participants/{deleted_participant_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Participant not found"},
    )
