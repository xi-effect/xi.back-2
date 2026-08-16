import pytest
from faker import Faker
from respx import MockRouter

from app.notifications.schemas.vk.vk_users_sch import UserFieldName, UserResponseSchema
from app.notifications.services.user_contact_syncers.vk_user_contact_syncer import (
    VKUserContactSyncer,
)
from tests.common.respx_ext import assert_last_httpx_request
from tests.notifications.factories import UserResponseFactory

pytestmark = pytest.mark.anyio


async def test_vk_user_contact_link_building(
    faker: Faker,
    active_vk_user_contact_syncer: VKUserContactSyncer,
) -> None:
    username: str = faker.user_name()

    assert (
        active_vk_user_contact_syncer.username_to_link(username=username)
        == f"https://vk.ru/{username}"
    )


@pytest.mark.parametrize(
    "has_username",
    [
        pytest.param(True, id="with_username"),
        pytest.param(False, id="no_username"),
    ],
)
async def test_vk_username_retrieving(
    faker: Faker,
    vk_respx_mock: MockRouter,
    active_vk_user_contact_syncer: VKUserContactSyncer,
    has_username: bool,
) -> None:
    user_data: UserResponseSchema = UserResponseFactory.build(
        screen_name=faker.user_name() if has_username else None
    )

    vk_get_users_mock = vk_respx_mock.post(path="/users.get").respond(
        json={"response": [user_data.model_dump(mode="json")]}
    )

    assert (
        await active_vk_user_contact_syncer.retrieve_current_username()
    ) == user_data.screen_name

    assert_last_httpx_request(
        vk_get_users_mock,
        expected_data={
            "user_ids": [str(active_vk_user_contact_syncer.delivery_method.peer_id)],
            "fields": [UserFieldName.SCREEN_NAME],
        },
    )


async def test_vk_username_retrieving_missing_user(
    vk_respx_mock: MockRouter,
    active_vk_user_contact_syncer: VKUserContactSyncer,
) -> None:
    vk_get_users_mock = vk_respx_mock.post(path="/users.get").respond(
        json={"response": []}
    )

    assert await active_vk_user_contact_syncer.retrieve_current_username() is None

    assert_last_httpx_request(
        vk_get_users_mock,
        expected_data={
            "user_ids": [str(active_vk_user_contact_syncer.delivery_method.peer_id)],
            "fields": [UserFieldName.SCREEN_NAME],
        },
    )
