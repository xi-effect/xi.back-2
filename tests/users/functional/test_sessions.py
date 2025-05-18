import pytest
from starlette.testclient import TestClient

from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import Factory
from tests.users.utils import assert_session, session_checker


@pytest.mark.anyio()
async def test_getting_current_session(
    authorized_client: TestClient,
    session: Session,
) -> None:
    assert_response(
        authorized_client.get("/api/protected/user-service/sessions/current/"),
        expected_json=session_checker(session),
    )


@pytest.mark.anyio()
async def test_signing_out(
    authorized_client: TestClient,
    active_session: ActiveSession,
    session_token: str,
) -> None:
    assert_nodata_response(
        authorized_client.delete("/api/protected/user-service/sessions/current/")
    )

    async with active_session():
        await assert_session(session_token, invalid=True)


@pytest.mark.anyio()
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


@pytest.mark.anyio()
async def test_disabling_session_non_found(
    authorized_client: TestClient, deleted_session_id: int
) -> None:
    assert_response(
        authorized_client.delete(
            f"/api/protected/user-service/sessions/{deleted_session_id}/"
        ),
        expected_code=404,
        expected_json={"detail": "Session not found"},
    )


@pytest.mark.anyio()
async def test_disabling_session_foreign_user(
    other_client: TestClient, session: Session
) -> None:
    assert_response(
        other_client.delete(f"/api/protected/user-service/sessions/{session.id}/"),
        expected_code=404,
        expected_json={"detail": "Session not found"},
    )


@pytest.fixture()
async def sessions(session_factory: Factory[Session]) -> list[Session]:
    return [await session_factory() for _ in range(2)][::-1]


@pytest.mark.anyio()
async def test_listing_sessions(
    authorized_client: TestClient,
    sessions: list[Session],
) -> None:
    assert_response(
        authorized_client.get("/api/protected/user-service/sessions/"),
        expected_json=[session_checker(session) for session in sessions],
    )


@pytest.mark.anyio()
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


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("use_headers", "error"),
    [
        pytest.param(False, "Authorization is missing", id="missing_header"),
        pytest.param(True, "Session is invalid", id="invalid_session"),
    ],
)
@pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param(
            "GET", "/api/protected/user-service/sessions/", id="list_sessions"
        ),
        pytest.param(
            "DELETE",
            "/api/protected/user-service/sessions/",
            id="delete_other_sessions",
        ),
        pytest.param(
            "GET",
            "/api/protected/user-service/sessions/current/",
            id="get_current_session",
        ),
        pytest.param(
            "DELETE",
            "/api/protected/user-service/sessions/current/",
            id="signout",
        ),
        pytest.param(
            "DELETE",
            "/api/protected/user-service/sessions/{session_id}/",
            id="disable_session",
        ),
    ],
)
async def test_sessions_unauthorized(
    client: TestClient,
    session: Session,
    invalid_token: str,
    use_headers: bool,
    error: str,
    method: str,
    path: str,
) -> None:
    cookies = {AUTH_COOKIE_NAME: invalid_token} if use_headers else {}
    assert_response(
        client.request(method, path.format(session_id=session.id), cookies=cookies),
        expected_code=401,
        expected_json={"detail": error},
    )
