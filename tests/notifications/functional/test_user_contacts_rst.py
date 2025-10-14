import random

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.models.user_contacts_db import UserContact
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.notifications.factories import UserContactInputFactory

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "is_public",
    [
        pytest.param(True, id="public"),
        pytest.param(False, id="private"),
    ],
)
async def test_user_contact_listing(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    random_contact_kind: UserContactKind,
    is_public: bool,
) -> None:
    async with active_session():
        user_contact = await UserContact.create(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
            **UserContactInputFactory.build_python(is_public=is_public),
        )

    assert_response(
        authorized_client.get(
            "/api/protected/notification-service/users/current/contacts/",
        ),
        expected_json=[
            UserContact.FullSchema.model_validate(
                user_contact, from_attributes=True
            ).model_dump(mode="json")
        ],
    )

    async with active_session():
        await UserContact.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
        )


@pytest.mark.parametrize(
    "is_public",
    [
        pytest.param(True, id="set_public"),
        pytest.param(False, id="set_private"),
    ],
)
async def test_updating_user_contact_visibility(
    authorized_client: TestClient,
    user_contact: UserContact,
    user_contact_data: AnyJSON,
    is_public: bool,
) -> None:
    assert_response(
        authorized_client.put(
            f"/api/protected/notification-service/users/current/contacts/{user_contact.kind}/visibility/",
            json={"is_public": is_public},
        ),
        expected_json={
            **user_contact_data,
            "is_public": is_public,
        },
    )


async def test_updating_user_contact_visibility_user_contact_not_found(
    authorized_client: TestClient,
    random_contact_kind: UserContactKind,
) -> None:
    assert_response(
        authorized_client.put(
            f"/api/protected/notification-service/users/current/contacts/{random_contact_kind}/visibility/",
            json={"is_public": random.choice([True, False])},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "User contact not found"},
    )
