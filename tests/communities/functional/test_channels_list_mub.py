import pytest
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values
from tests.communities import factories
from tests.communities.conftest import CHANNEL_LIST_SIZE

pytestmark = pytest.mark.anyio


async def test_reindexing_channels(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
    category: Category,
    channel_parent_category_id: int | None,
) -> None:
    channels_count = 3

    async with active_session() as db_session:
        db_session.add_all(
            Channel(
                community_id=community.id,
                category_id=channel_parent_category_id,
                position=i,
                **factories.ChannelInputFactory.build_json(),
            )
            for i in range(channels_count)
        )

    assert_nodata_response(
        mub_client.put(
            f"/mub/community-service/communities/{community.id}/channels/positions/",
            params=remove_none_values({"category_id": channel_parent_category_id}),
        )
    )

    async with active_session():
        channels = await Channel.find_all_by_kwargs(
            Channel.position,
            community_id=community.id,
            category_id=channel_parent_category_id,
        )
        positions = [channel.position for channel in channels]
        assert_contains(positions, [i * Channel.spacing for i in range(channels_count)])

        for channel in channels:
            await channel.delete()


async def test_channels_listing(
    mub_client: TestClient,
    community: Community,
    category: Category,
    category_data: AnyJSON,
    channels_without_category_data: list[AnyJSON],
    channels_with_category_data: list[AnyJSON],
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/communities/{community.id}/channels/"),
        expected_json=[
            {
                "category": None,
                "channels": channels_without_category_data,
            },
            {
                "category": {**category_data, "id": category.id},
                "channels": channels_with_category_data,
            },
        ],
    )


@pytest.mark.parametrize(
    ("target", "after", "before"),
    [
        pytest.param(2, None, 0, id="middle_to_start"),
        pytest.param(2, CHANNEL_LIST_SIZE - 1, None, id="middle_to_end"),
        pytest.param(0, 2, 3, id="start_to_middle"),
    ],
)
async def test_channel_moving(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
    category: Category,
    channel_parent_category_id: int | None,
    channels_without_category_data: list[AnyJSON],
    channels_with_category_data: list[AnyJSON],
    target: int,
    after: int | None,
    before: int | None,
) -> None:
    channels_data = list(
        channels_without_category_data
        if channel_parent_category_id is None
        else channels_with_category_data
    )
    channel_ids = [channel_data["id"] for channel_data in channels_data]

    assert_nodata_response(
        mub_client.put(
            f"/mub/community-service/channels/{channel_ids[target]}/position/",
            json={
                "category_id": channel_parent_category_id,
                "after_id": None if after is None else channel_ids[after],
                "before_id": None if before is None else channel_ids[before],
            },
        ),
    )

    if before is None:
        channel_ids.append(channel_ids.pop(target))
    elif target < before:
        channel_ids.insert(before - 1, channel_ids.pop(target))
    else:
        channel_ids.insert(before, channel_ids.pop(target))

    async with active_session():
        assert [  # noqa: WPS309  # WPS bug
            channel.id
            for channel in await Channel.find_all_by_kwargs(
                Channel.position,
                community_id=community.id,
                category_id=channel_parent_category_id,
            )
        ] == channel_ids
