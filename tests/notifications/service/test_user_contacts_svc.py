import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services import user_contacts_svc
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.notifications.factories import UserContactInputFactory

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "has_existing_user_contact",
    [
        pytest.param(True, id="existed_before"),
        pytest.param(False, id="never_existed"),
    ],
)
async def test_personal_telegram_contact_removing(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    has_existing_user_contact: bool,
) -> None:
    if has_existing_user_contact:
        async with active_session():
            await UserContact.create(
                user_id=proxy_auth_data.user_id,
                kind=UserContactKind.PERSONAL_TELEGRAM,
                **UserContactInputFactory.build_python(),
            )

    async with active_session():
        await user_contacts_svc.remove_personal_telegram_contact(
            user_id=proxy_auth_data.user_id,
        )

    async with active_session():
        assert (
            await UserContact.find_first_by_primary_key(
                user_id=proxy_auth_data.user_id,
                kind=UserContactKind.PERSONAL_TELEGRAM,
            )
        ) is None


async def test_personal_telegram_contact_syncing_empty_username(
    mock_stack: MockStack,
    proxy_auth_data: ProxyAuthData,
) -> None:
    remove_personal_telegram_contact_mock = mock_stack.enter_async_mock(
        user_contacts_svc, "remove_personal_telegram_contact"
    )

    user_contact = await user_contacts_svc.sync_personal_telegram_contact(
        user_id=proxy_auth_data.user_id,
        new_username=None,
    )
    assert user_contact is None

    remove_personal_telegram_contact_mock.assert_awaited_once_with(
        user_id=proxy_auth_data.user_id
    )


@pytest.mark.parametrize(
    ("is_existing_contact_public", "expected_is_public"),
    [
        pytest.param(None, True, id="never_existed"),
        pytest.param(True, True, id="existed_before-public"),
        pytest.param(False, False, id="existed_before-private"),
    ],
)
async def test_personal_telegram_contact_syncing(
    faker: Faker,
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    is_existing_contact_public: bool | None,
    expected_is_public: bool,
) -> None:
    if is_existing_contact_public is not None:
        async with active_session():
            await UserContact.create(
                user_id=proxy_auth_data.user_id,
                kind=UserContactKind.PERSONAL_TELEGRAM,
                **UserContactInputFactory.build_python(
                    is_public=is_existing_contact_public
                ),
            )

    new_username: str = faker.user_name()

    async with active_session():
        user_contact = await user_contacts_svc.sync_personal_telegram_contact(
            user_id=proxy_auth_data.user_id,
            new_username=new_username,
        )
        assert user_contact is not None
        assert_contains(
            user_contact,
            {
                "user_id": proxy_auth_data.user_id,
                "kind": UserContactKind.PERSONAL_TELEGRAM,
                "title": f"@{new_username}",
                "link": f"https://t.me/{new_username}",
                "is_public": expected_is_public,
            },
        )
        await user_contact.delete()
