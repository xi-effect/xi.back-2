import pytest
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import Factory
from tests.factories import ProxyAuthDataFactory
from tests.users.utils import session_checker

pytestmark = pytest.mark.anyio


async def test_getting_current_session(
    authorized_client: TestClient,
    session: Session,
) -> None:
    assert_response(
        authorized_client.get("/api/protected/user-service/sessions/current/"),
        expected_json=session_checker(session),
    )


async def test_signing_out(
    authorized_client: TestClient,
    active_session: ActiveSession,
    user_proxy_auth_data: ProxyAuthData,
) -> None:
    assert_nodata_response(
        authorized_client.delete("/api/protected/user-service/sessions/current/")
    )

    async with active_session():
        session = await Session.find_first_by_id(user_proxy_auth_data.session_id)
        assert session is not None
        assert session.is_invalid


async def test_disabling_session(
    active_session: ActiveSession,
    authorized_client: TestClient,
    session: Session,
) -> None:
    assert_nodata_response(
        authorized_client.delete(f"/api/protected/user-service/sessions/{session.id}/")
    )
    async with active_session():
        db_session = await Session.find_first_by_id(session.id)
        assert db_session is not None
        assert db_session.is_invalid


@pytest.fixture()
async def deleted_session_id(
    active_session: ActiveSession,
    session_factory: Factory[Session],
) -> int:
    session = await session_factory()
    async with active_session():
        await session.delete()
    return session.id


async def test_disabling_session_non_found(
    authorized_client: TestClient, deleted_session_id: int
) -> None:
    assert_response(
        authorized_client.delete(
            f"/api/protected/user-service/sessions/{deleted_session_id}/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Session not found"},
    )


async def test_disabling_session_foreign_user(
    other_client: TestClient, session: Session
) -> None:
    assert_response(
        other_client.delete(f"/api/protected/user-service/sessions/{session.id}/"),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Session not found"},
    )


@pytest.fixture()
async def sessions(session_factory: Factory[Session]) -> list[Session]:
    return [await session_factory() for _ in range(2)][::-1]


async def test_listing_sessions(
    authorized_client: TestClient,
    sessions: list[Session],
) -> None:
    assert_response(
        authorized_client.get("/api/protected/user-service/sessions/"),
        expected_json=[session_checker(session) for session in sessions],
    )


async def test_disabling_all_other_sessions(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
    session: Session,
) -> None:
    assert_nodata_response(
        authorized_client.delete("/api/protected/user-service/sessions/")
    )
    async with active_session():
        for db_session in await Session.find_by_user(user.id, exclude_id=session.id):
            assert db_session.is_invalid


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("GET", id="get-current-session"),
        pytest.param("DELETE", id="signout"),
    ],
)
async def test_requesting_current_session_not_found(
    client: TestClient,
    user_proxy_auth_data: ProxyAuthData,
    deleted_session_id: int,
    method: str,
) -> None:
    broken_proxy_auth_data: ProxyAuthData = ProxyAuthDataFactory.build(
        session_id=deleted_session_id,
        user_id=user_proxy_auth_data.user_id,
    )

    assert_response(
        client.request(
            method,
            "/api/protected/user-service/sessions/current/",
            headers=broken_proxy_auth_data.as_headers,
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Session not found"},
    )
