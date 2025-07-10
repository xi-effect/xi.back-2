import random
from collections.abc import AsyncIterator
from typing import cast

import pytest

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications.models.user_contacts_db import ContactKind, UserContact
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.notifications import factories


@pytest.fixture()
def random_contact_kind() -> ContactKind:
    # mypy gets confused, the real type is ContactKind
    return cast(ContactKind, random.choice(list(ContactKind)))


@pytest.fixture()
async def user_contact(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    random_contact_kind: ContactKind,
) -> AsyncIterator[UserContact]:
    async with active_session():
        user_contact = await UserContact.create(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
            **factories.UserContactInputFactory.build_python(),
        )

    yield user_contact

    async with active_session():
        await UserContact.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
        )


@pytest.fixture()
async def user_contact_data(user_contact: UserContact) -> AnyJSON:
    return UserContact.FullSchema.model_validate(
        user_contact, from_attributes=True
    ).model_dump(mode="json")
