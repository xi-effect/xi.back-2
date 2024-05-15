from random import randint

import pytest

from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from app.communities.models.participants_db import Participant
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.communities import factories


@pytest.fixture()
async def community_data() -> AnyJSON:
    return factories.CommunityFullInputFactory.build_json()


@pytest.fixture()
async def community(
    active_session: ActiveSession,
    community_data: AnyJSON,
) -> Community:
    async with active_session():
        return await Community.create(**community_data)


@pytest.fixture()
async def deleted_community_id(
    active_session: ActiveSession,
    community: Community,
) -> int:
    async with active_session():
        await community.delete()
    return community.id


@pytest.fixture()
async def participant_user_id() -> int:
    return randint(0, 10000)


@pytest.fixture()
async def participant(
    active_session: ActiveSession,
    community: Community,
    participant_user_id: int,
) -> Participant:
    async with active_session():
        return await Participant.create(
            community_id=community.id,
            user_id=participant_user_id,
        )


@pytest.fixture()
def participant_data(participant: Participant) -> AnyJSON:
    return Participant.FullResponseSchema.model_validate(
        participant, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_participant_id(
    active_session: ActiveSession,
    participant: Participant,
) -> int:
    async with active_session():
        await participant.delete()
    return participant.id


@pytest.fixture()
async def invitation(
    active_session: ActiveSession,
    community: Community,
) -> Invitation:
    async with active_session():
        return await Invitation.create(
            community_id=community.id,
            **factories.InvitationFullInputFactory.build_json()
        )


@pytest.fixture()
def invitation_data(invitation: Invitation) -> AnyJSON:
    return Invitation.FullResponseSchema.model_validate(
        invitation, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_invitation_id(
    active_session: ActiveSession,
    invitation: Invitation,
) -> int:
    async with active_session():
        await invitation.delete()
    return invitation.id


@pytest.fixture()
async def category_data() -> AnyJSON:
    return factories.CategoryInputFactory.build_json()


@pytest.fixture()
async def category(
    active_session: ActiveSession,
    community: Community,
    category_data: AnyJSON,
) -> Category:
    async with active_session():
        return await Category.create(community_id=community.id, **category_data)


@pytest.fixture()
async def deleted_category_id(
    active_session: ActiveSession,
    category: Category,
) -> int:
    async with active_session():
        await category.delete()
    return category.id


@pytest.fixture()
async def channel_data() -> AnyJSON:
    return factories.ChannelInputFactory.build_json()


@pytest.fixture()
async def channel(
    active_session: ActiveSession,
    community: Community,
    channel_data: AnyJSON,
) -> Channel:
    async with active_session():
        return await Channel.create(community_id=community.id, **channel_data)


@pytest.fixture()
async def deleted_channel_id(
    active_session: ActiveSession,
    channel: Channel,
) -> int:
    async with active_session():
        await channel.delete()
    return channel.id
