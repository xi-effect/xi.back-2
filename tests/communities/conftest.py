import pytest

from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.communities.factories import CommunityFullInputFactory


@pytest.fixture()
async def community_data() -> AnyJSON:
    return CommunityFullInputFactory.build().model_dump(mode="json")


@pytest.fixture()
async def community(
    active_session: ActiveSession,
    community_data: AnyJSON,
) -> Community:
    async with active_session():
        return await Community.create(**community_data)
