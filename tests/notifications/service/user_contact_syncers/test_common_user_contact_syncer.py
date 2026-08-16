from typing import Any

import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf

from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services.user_contact_syncers import base_user_contact_syncer
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.notifications import factories

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("user_contact_syncer", "existing_user_contact"),
    [
        pytest.param(
            lf("active_telegram_user_contact_syncer"),
            None,
            id="telegram-no_user_contact",
        ),
        pytest.param(
            lf("active_telegram_user_contact_syncer"),
            lf("personal_telegram_user_contact"),
            id="telegram-with_user_contact",
        ),
        pytest.param(
            lf("active_vk_user_contact_syncer"),
            None,
            id="vk-no_user_contact",
        ),
        pytest.param(
            lf("active_vk_user_contact_syncer"),
            lf("personal_vk_user_contact"),
            id="vk-with_user_contact",
        ),
    ],
)
async def test_user_contact_removing(
    active_session: ActiveSession,
    user_contact_syncer: base_user_contact_syncer.BaseUserContactSyncer[Any],
    existing_user_contact: UserContact | None,
) -> None:
    async with active_session():
        await user_contact_syncer.remove()

    async with active_session():
        assert (
            await UserContact.find_first_by_primary_key(
                user_id=user_contact_syncer.delivery_method.user_id,
                kind=user_contact_syncer.contact_kind,
            )
        ) is None


@pytest.mark.parametrize(
    ("is_existing_user_contact_public", "is_expected_to_be_public"),
    [
        pytest.param(None, True, id="no_user_contact"),
        pytest.param(True, True, id="with_public_user_contact"),
        pytest.param(False, False, id="with_private_user_contact"),
    ],
)
@pytest.mark.parametrize(
    "user_contact_syncer",
    [
        pytest.param(lf("active_telegram_user_contact_syncer"), id="telegram"),
        pytest.param(lf("active_vk_user_contact_syncer"), id="vk"),
    ],
)
async def test_user_contact_upserting_from_username(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    user_contact_syncer: base_user_contact_syncer.BaseUserContactSyncer[Any],
    is_existing_user_contact_public: bool | None,
    is_expected_to_be_public: bool,
) -> None:
    username: str = faker.user_name()
    expected_link: str = faker.url()
    username_to_link_mock = mock_stack.enter_mock(
        user_contact_syncer,
        "username_to_link",
        return_value=expected_link,
    )

    if is_existing_user_contact_public is not None:
        async with active_session():
            await UserContact.create(
                user_id=user_contact_syncer.delivery_method.user_id,
                kind=user_contact_syncer.contact_kind,
                **factories.UserContactInputFactory.build_python(
                    is_public=is_existing_user_contact_public,
                ),
            )

    async with active_session():
        user_contact = await user_contact_syncer.upsert_from_username(
            username=username,
        )

    assert_contains(
        user_contact,
        {
            "user_id": user_contact_syncer.delivery_method.user_id,
            "kind": user_contact_syncer.contact_kind,
            "link": expected_link,
            "title": f"@{username}",
            "is_public": is_expected_to_be_public,
        },
    )

    username_to_link_mock.assert_called_once_with(username=username)

    async with active_session():
        await UserContact.delete_by_kwargs(
            user_id=user_contact_syncer.delivery_method.user_id,
            kind=user_contact_syncer.contact_kind,
        )


@pytest.mark.parametrize(
    "has_username",
    [
        pytest.param(True, id="with_username"),
        pytest.param(False, id="no_username"),
    ],
)
@pytest.mark.parametrize(
    ("user_contact_syncer", "existing_user_contact"),
    [
        pytest.param(
            lf("active_telegram_user_contact_syncer"),
            lf("personal_telegram_user_contact"),
            id="telegram",
        ),
        pytest.param(
            lf("active_vk_user_contact_syncer"),
            lf("personal_vk_user_contact"),
            id="vk",
        ),
    ],
)
async def test_user_contact_syncing_with_origin(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    user_contact_syncer: base_user_contact_syncer.BaseUserContactSyncer[Any],
    existing_user_contact: UserContact,
    has_username: bool,
) -> None:
    username: str | None = faker.user_name() if has_username else None
    retrieve_current_username_mock = mock_stack.enter_async_mock(
        user_contact_syncer,
        "retrieve_current_username",
        return_value=username,
    )
    expected_link: str = faker.url()
    username_to_link_mock = mock_stack.enter_mock(
        user_contact_syncer,
        "username_to_link",
        return_value=expected_link,
    )

    async with active_session():
        user_contact = await user_contact_syncer.sync_with_origin()

    async with active_session():
        stored_user_contact = await UserContact.find_first_by_primary_key(
            user_id=user_contact_syncer.delivery_method.user_id,
            kind=user_contact_syncer.contact_kind,
        )

    if username is None:
        assert user_contact is None
        assert stored_user_contact is None
        username_to_link_mock.assert_not_called()
    else:
        assert user_contact is not None
        assert stored_user_contact is not None
        assert_contains(
            user_contact,
            {
                "link": expected_link,
                "title": f"@{username}",
            },
        )
        username_to_link_mock.assert_called_once_with(username=username)

    retrieve_current_username_mock.assert_awaited_once_with()
