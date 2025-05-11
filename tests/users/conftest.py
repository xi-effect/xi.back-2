from typing import Any

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from app.common.config import settings
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME, AUTH_HEADER_NAME
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
async def user_data() -> AnyJSON:
    return factories.UserInputFactory.build_json()


@pytest.fixture()
async def user(
    user_factory: Factory[User],
    user_data: AnyJSON,
) -> User:
    return await user_factory(**user_data)


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
async def deleted_user(
    active_session: ActiveSession,
    user_factory: Factory[User],
) -> User:
    user = await user_factory(**factories.UserInputFactory.build_json())
    async with active_session():
        await user.delete()
    return user


@pytest.fixture()
async def session_factory(
    active_session: ActiveSession, user: User
) -> Factory[Session]:  # TODO used in unit tests for users
    async def session_factory_inner(**kwargs: Any) -> Session:
        async with active_session():
            return await Session.create(user_id=user.id, **kwargs)

    return session_factory_inner


@pytest.fixture()
async def session(session_factory: Factory[Session]) -> Session:
    return await session_factory()


@pytest.fixture()
def session_token(session: Session) -> str:
    return session.token


@pytest.fixture(params=[False, True], ids=["headers", "cookies"])
def use_cookie_auth(request: PytestRequest[bool]) -> bool:
    return request.param


@pytest.fixture()
def authorized_client(
    client: TestClient,
    session_token: str,
    use_cookie_auth: bool,
) -> TestClient:
    if use_cookie_auth:
        return TestClient(
            client.app,
            base_url=f"http://{settings.cookie_domain}",
            cookies={AUTH_COOKIE_NAME: session_token},
        )
    return TestClient(
        client.app,
        base_url=f"http://{settings.cookie_domain}",
        headers={AUTH_HEADER_NAME: session_token},
    )


@pytest.fixture()
async def other_session(active_session: ActiveSession, other_user: User) -> Session:
    async with active_session():
        return await Session.create(user_id=other_user.id)


@pytest.fixture()
def other_session_token(other_session: Session) -> str:
    return other_session.token


@pytest.fixture()
def other_client(client: TestClient, other_session_token: str) -> TestClient:
    return TestClient(
        client.app,
        base_url=f"http://{settings.cookie_domain}",
        cookies={AUTH_COOKIE_NAME: other_session_token},
    )


@pytest.fixture()
async def invalid_session(session_factory: Factory[Session]) -> Session:
    return await session_factory(is_disabled=True)


@pytest.fixture()
def invalid_token(invalid_session: Session) -> str:
    return invalid_session.token


@pytest.fixture(params=[True, False])
def invalid_mub_key_headers(
    request: PytestRequest[bool], faker: Faker
) -> dict[str, Any] | None:
    if request.param:
        return {"X-MUB-Secret": faker.pystr()}
    return None
