import pytest
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications.models.user_contacts_db import ContactKind, UserContact
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.notifications.factories import UserContactInputFactory

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("public_only", "is_public", "is_listed"),
    [
        pytest.param(True, True, True, id="public_only-public"),
        pytest.param(True, False, False, id="public_only-private"),
        pytest.param(False, True, True, id="all-public"),
        pytest.param(False, False, True, id="all-private"),
    ],
)
async def test_user_contact_listing(
    active_session: ActiveSession,
    internal_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    random_contact_kind: ContactKind,
    public_only: bool,
    is_public: bool,
    is_listed: bool,
) -> None:
    async with active_session():
        user_contact = await UserContact.create(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
            **UserContactInputFactory.build_python(is_public=is_public),
        )

    user_contact_data = UserContact.FullSchema.model_validate(
        user_contact, from_attributes=True
    ).model_dump(mode="json")
    assert_response(
        internal_client.get(
            f"/internal/notification-service/users/{proxy_auth_data.user_id}/contacts/",
            params={"public_only": public_only},
        ),
        expected_json=[user_contact_data] if is_listed else [],
    )

    async with active_session():
        await UserContact.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
        )


async def test_user_contact_creation(
    active_session: ActiveSession,
    internal_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    random_contact_kind: ContactKind,
) -> None:
    user_contact_input_data = UserContactInputFactory.build_json()

    assert_response(
        internal_client.put(
            f"/internal/notification-service/users/{proxy_auth_data.user_id}/contacts/{random_contact_kind}/",
            json=user_contact_input_data,
        ),
        expected_json={
            **user_contact_input_data,
            "kind": random_contact_kind,
        },
    )

    async with active_session():
        user_contact = await UserContact.find_first_by_primary_key(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
        )
        assert user_contact is not None
        await user_contact.delete()


async def test_user_contact_updating(
    internal_client: TestClient,
    user_contact: UserContact,
) -> None:
    user_contact_input_data = UserContactInputFactory.build_json()

    assert_response(
        internal_client.put(
            f"/internal/notification-service/users/{user_contact.user_id}/contacts/{user_contact.kind}/",
            json=user_contact_input_data,
        ),
        expected_json={
            **user_contact_input_data,
            "kind": user_contact.kind,
        },
    )


async def test_user_contact_deleting(
    active_session: ActiveSession,
    internal_client: TestClient,
    user_contact: UserContact,
) -> None:
    assert_nodata_response(
        internal_client.delete(
            f"/internal/notification-service/users/{user_contact.user_id}/contacts/{user_contact.kind}/",
        )
    )

    async with active_session():
        assert (
            await UserContact.find_first_by_primary_key(
                user_id=user_contact.user_id,
                kind=user_contact.kind,
            )
        ) is None


async def test_user_contact_deleting_user_contact_not_found(
    internal_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    random_contact_kind: ContactKind,
) -> None:
    assert_response(
        internal_client.delete(
            f"/internal/notification-service/users/{proxy_auth_data.user_id}/contacts/{random_contact_kind}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "User contact not found"},
    )
