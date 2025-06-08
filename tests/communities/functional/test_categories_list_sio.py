import pytest
from starlette import status

from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.communities.conftest import CATEGORY_LIST_SIZE

pytestmark = pytest.mark.anyio


async def test_categories_listing(
    community: Community,
    tmexio_participant_client: TMEXIOTestClient,
    categories_data: list[AnyJSON],
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            "list-categories",
            community_id=community.id,
        ),
        expected_data=categories_data,
    )
    tmexio_participant_client.assert_no_more_events()


@pytest.mark.parametrize(
    ("target", "after", "before"),
    [
        pytest.param(2, None, 0, id="middle_to_start"),
        pytest.param(2, CATEGORY_LIST_SIZE - 1, None, id="middle_to_end"),
        pytest.param(0, 2, 3, id="start_to_middle"),
    ],
)
async def test_category_moving(
    active_session: ActiveSession,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    categories_data: list[AnyJSON],
    target: int,
    after: int | None,
    before: int | None,
) -> None:
    category_ids = [category_data["id"] for category_data in categories_data]

    assert_ack(
        await tmexio_owner_client.emit(
            "move-category",
            community_id=community.id,
            category_id=category_ids[target],
            after_id=None if after is None else category_ids[after],
            before_id=None if before is None else category_ids[before],
        ),
        expected_code=204,
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="move-category",
        expected_data={
            "community_id": community.id,
            "category_id": category_ids[target],
            "after_id": None if after is None else category_ids[after],
            "before_id": None if before is None else category_ids[before],
        },
    )
    community_room_listener.assert_no_more_events()

    if before is None:
        category_ids.append(category_ids.pop(target))
    elif target < before:
        category_ids.insert(before - 1, category_ids.pop(target))
    else:
        category_ids.insert(before, category_ids.pop(target))

    async with active_session():
        assert [  # noqa: WPS309  # WPS bug
            category.id
            for category in await Category.find_all_by_community_id(
                community_id=community.id
            )
        ] == category_ids


async def test_category_moving_category_not_found(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    deleted_category_id: int,
    channel: Channel,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "move-category",
            community_id=community.id,
            channel_id=channel.id,
            category_id=deleted_category_id,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Category not found",
    )
    tmexio_owner_client.assert_no_more_events()


async def test_category_moving_not_sufficient_permissions(
    community: Community,
    tmexio_participant_client: TMEXIOTestClient,
    category: Category,
    channel: Channel,
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            "move-category",
            community_id=community.id,
            channel_id=channel.id,
            category_id=category.id,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="Not sufficient permissions",
    )
    tmexio_participant_client.assert_no_more_events()


@pytest.mark.parametrize(
    "event_name",
    [
        pytest.param("list-categories", id="list"),
        pytest.param("move-category", id="move"),
    ],
)
async def test_categories_requesting_community_not_finding(
    deleted_community_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=deleted_community_id,
            channel_id=1,
            category_id=1,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()


@pytest.mark.parametrize(
    "event_name",
    [
        pytest.param("list-categories", id="list"),
        pytest.param("move-category", id="move"),
    ],
)
async def test_categories_requesting_no_access_to_community(
    community: Community,
    tmexio_outsider_client: TMEXIOTestClient,
    category: Category,
    channel: Channel,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=community.id,
            channel_id=channel.id,
            category_id=category.id,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="No access to community",
    )
    tmexio_outsider_client.assert_no_more_events()
