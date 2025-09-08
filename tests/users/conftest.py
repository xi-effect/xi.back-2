from typing import Any

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.users_sch import UserProfileSchema
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, Factory, PytestRequest
from tests.users import factories


@pytest.fixture(scope="session")
async def user_factory(active_session: ActiveSession) -> Factory[User]:
    async def session_factory_inner(**kwargs: Any) -> User:
        kwargs["password"] = User.generate_hash(kwargs["password"])

        async with active_session():
            return await User.create(**kwargs)

    return session_factory_inner


@pytest.fixture()
async def session_factory(
    active_session: ActiveSession, user: User
) -> Factory[Session]:
    async def session_factory_inner(**kwargs: Any) -> Session:
        async with active_session():
            return await Session.create(user_id=user.id, **kwargs)

    return session_factory_inner


@pytest.fixture()
async def user_data() -> AnyJSON:
    return factories.UserInputFactory.build_json()


@pytest.fixture()
async def user(
    user_factory: Factory[User],
    user_data: AnyJSON,
) -> User:
    return await user_factory(**user_data)


@pytest.fixture()
async def user_profile_data(user: User) -> AnyJSON:
    return UserProfileSchema.model_validate(user, from_attributes=True).model_dump(
        mode="json"
    )


@pytest.fixture()
async def session(session_factory: Factory[Session]) -> Session:
    return await session_factory()


@pytest.fixture()
async def user_proxy_auth_data(user: User, session: Session) -> ProxyAuthData:
    return ProxyAuthData(
        user_id=user.id,
        username=user.username,
        session_id=session.id,
    )


@pytest.fixture()
def authorized_client(
    client: TestClient,
    user_proxy_auth_data: ProxyAuthData,
) -> TestClient:
    return TestClient(client.app, headers=user_proxy_auth_data.as_headers)


@pytest.fixture()
async def other_user_data() -> AnyJSON:
    return factories.UserInputFactory.build_json()


@pytest.fixture()
async def other_user(
    user_factory: Factory[User],
    other_user_data: AnyJSON,
) -> User:
    return await user_factory(**other_user_data)


@pytest.fixture()
async def other_user_profile_data(other_user: User) -> AnyJSON:
    return UserProfileSchema.model_validate(
        other_user, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def other_session(active_session: ActiveSession, other_user: User) -> Session:
    async with active_session():
        return await Session.create(user_id=other_user.id)


@pytest.fixture()
async def other_user_proxy_auth_data(
    other_user: User, other_session: Session
) -> ProxyAuthData:
    return ProxyAuthData(
        user_id=other_user.id,
        username=other_user.username,
        session_id=other_session.id,
    )


@pytest.fixture()
def other_client(
    client: TestClient,
    other_user_proxy_auth_data: ProxyAuthData,
) -> TestClient:
    return TestClient(client.app, headers=other_user_proxy_auth_data.as_headers)


@pytest.fixture()
async def deleted_user_id(
    active_session: ActiveSession,
    user_factory: Factory[User],
) -> int:
    user = await user_factory(**factories.UserInputFactory.build_json())
    async with active_session():
        await user.delete()
    return user.id


@pytest.fixture()
async def invalid_session(session_factory: Factory[Session]) -> Session:
    return await session_factory(is_disabled=True)


@pytest.fixture()
def invalid_token(invalid_session: Session) -> str:
    return invalid_session.token


@pytest.fixture()
async def deleted_session_id(
    active_session: ActiveSession,
    session_factory: Factory[Session],
) -> int:
    session = await session_factory()
    async with active_session():
        await session.delete()
    return session.id


@pytest.fixture(params=[True, False])
def invalid_mub_key_headers(
    request: PytestRequest[bool], faker: Faker
) -> dict[str, Any] | None:
    if request.param:
        return {"X-MUB-Secret": faker.pystr()}
    return None
