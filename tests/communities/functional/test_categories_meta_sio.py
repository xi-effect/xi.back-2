from typing import Any

import pytest
from starlette import status

from app.communities.models.categories_db import Category
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.communities import factories

pytestmark = pytest.mark.anyio


async def test_category_creation(
    active_session: ActiveSession,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    category_data: AnyJSON,
) -> None:
    category_id: int = assert_ack(
        await tmexio_owner_client.emit(
            "create-category",
            community_id=community.id,
            data=category_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_data={**category_data, "id": int},
    )[1]["id"]
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="create-category",
        expected_data={**category_data, "id": category_id},
    )
    community_room_listener.assert_no_more_events()

    async with active_session():
        category = await Category.find_first_by_id(category_id)
        assert category is not None
        await category.delete()


async def test_category_creation_quantity_exceeded(
    mock_stack: MockStack,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    category_data: AnyJSON,
) -> None:
    mock_stack.enter_mock(Category, "max_count_per_community", property_value=0)
    assert_ack(
        await tmexio_owner_client.emit(
            "create-category",
            community_id=community.id,
            data=category_data,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_data="Quantity limit exceeded",
    )
    tmexio_owner_client.assert_no_more_events()
    community_room_listener.assert_no_more_events()


async def test_category_updating(
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    category: Community,
    category_data: AnyJSON,
) -> None:
    category_patch_data = factories.CategoryPatchFactory.build_json()

    assert_ack(
        await tmexio_owner_client.emit(
            "update-category",
            community_id=community.id,
            category_id=category.id,
            data=category_patch_data,
        ),
        expected_data={**category_data, **category_patch_data, "id": category.id},
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="update-category",
        expected_data={**category_data, **category_patch_data, "id": category.id},
    )
    community_room_listener.assert_no_more_events()


async def test_category_deleting(
    active_session: ActiveSession,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    category: Category,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "delete-category",
            community_id=community.id,
            category_id=category.id,
        ),
        expected_code=status.HTTP_204_NO_CONTENT,
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="delete-category",
        expected_data={"community_id": community.id, "category_id": category.id},
    )
    community_room_listener.assert_no_more_events()

    async with active_session():
        assert (await Category.find_first_by_id(category.id)) is None


category_events_params = [
    pytest.param("create-category", factories.CategoryInputFactory, id="create"),
    pytest.param("update-category", factories.CategoryPatchFactory, id="update"),
    pytest.param("delete-category", None, id="delete"),
]


@pytest.mark.parametrize(("event_name", "data_factory"), category_events_params)
async def test_managing_categories_community_not_found(
    deleted_community_id: int,
    community_room_listener: TMEXIOTestClient,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=deleted_community_id,
            category_id=1,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()
    community_room_listener.assert_no_more_events()


@pytest.mark.parametrize(("event_name", "data_factory"), category_events_params)
async def test_managing_categories_no_access_to_community(
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=community.id,
            category_id=1,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="No access to community",
    )
    tmexio_outsider_client.assert_no_more_events()
    community_room_listener.assert_no_more_events()


@pytest.mark.parametrize(
    ("event_name", "data_factory"),
    [param for param in category_events_params if param.id != "create"],
)
async def test_managing_categories_category_not_found(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    community_room_listener: TMEXIOTestClient,
    deleted_category_id: int,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            event_name,
            community_id=community.id,
            category_id=deleted_category_id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Category not found",
    )
    tmexio_owner_client.assert_no_more_events()
    community_room_listener.assert_no_more_events()


@pytest.mark.parametrize(("event_name", "data_factory"), category_events_params)
async def test_managing_categories_insufficient_permissions(
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_participant_client: TMEXIOTestClient,
    category: Category,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            event_name,
            community_id=community.id,
            category_id=category.id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="Not sufficient permissions",
    )
    tmexio_participant_client.assert_no_more_events()
    community_room_listener.assert_no_more_events()
