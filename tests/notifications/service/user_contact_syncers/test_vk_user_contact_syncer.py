import pytest
from faker import Faker

from app.notifications.services.user_contact_syncers.vk_user_contact_syncer import (
    VKUserContactSyncer,
)

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
