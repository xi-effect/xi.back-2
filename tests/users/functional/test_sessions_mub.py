from datetime import datetime
from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.users.models.sessions_db import Session
from app.users.models.users_db import User
from app.users.utils.authorization import AUTH_COOKIE_NAME
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import Factory
from tests.users.utils import (
    assert_session_from_cookie,
    get_db_session,
    session_checker,
)


@pytest.fixture()
async def mub_session(session_factory: Factory[Session]) -> Session:
    return await session_factory(is_mub=True)


@pytest.mark.anyio()
async def test_making_mub_session(
    active_session: ActiveSession,
    mub_client: TestClient,
    user: User,
) -> None:
    response = assert_nodata_response(
        mub_client.post(f"/mub/user-service/users/{user.id}/sessions/"),
        expected_code=201,
        expected_cookies={AUTH_COOKIE_NAME: str},
        expected_headers={
            "X-Session-ID": int,
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-Cookie": AUTH_COOKIE_NAME,
            "X-Session-Token": str,
        },
    )

    async with active_session():
        session = await assert_session_from_cookie(response)
        assert_contains(
            {
                "is_mub": session.is_mub,
                "user_id": session.user_id,
                "is_invalid": session.is_invalid,
                "id": session.id,
                "token": session.token,
            },
            {
                "is_mub": True,
                "user_id": user.id,
                "is_invalid": False,
                "id": int(response.headers["X-Session-ID"]),
                "token": response.headers["X-Session-Token"],
            },
        )


@pytest.mark.anyio()
async def test_upserting_mub_session(
    active_session: ActiveSession,
    mub_client: TestClient,
    user: User,
) -> None:
    response = assert_nodata_response(
        mub_client.put(f"/mub/user-service/users/{user.id}/sessions/"),
        expected_cookies={AUTH_COOKIE_NAME: str},
        expected_headers={
            "X-Session-ID": int,
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-Cookie": AUTH_COOKIE_NAME,
            "X-Session-Token": str,
        },
    )

    async with active_session():
        session = await assert_session_from_cookie(response)
        assert_contains(
            {
                "is_mub": session.is_mub,
                "user_id": session.user_id,
                "is_invalid": session.is_invalid,
                "id": session.id,
                "token": session.token,
            },
            {
                "is_mub": True,
                "user_id": user.id,
                "is_invalid": False,
                "id": int(response.headers["X-Session-ID"]),
                "token": response.headers["X-Session-Token"],
            },
        )


@pytest.mark.anyio()
async def test_upserting_existing_mub_session(
    mub_client: TestClient,
    user: User,
    mub_session: Session,
) -> None:
    assert_nodata_response(
        mub_client.put(f"/mub/user-service/users/{user.id}/sessions/"),
        expected_cookies={AUTH_COOKIE_NAME: mub_session.token},
        expected_headers={
            "X-Session-ID": str(mub_session.id),
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-Cookie": AUTH_COOKIE_NAME,
            "X-Session-Token": mub_session.token,
        },
    )


@pytest.mark.anyio()
async def test_upserting_expired_mub_session(
    active_session: ActiveSession,
    session_factory: Factory[Session],
    mub_client: TestClient,
    user: User,
) -> None:
    await session_factory(is_mub=True, expires_at=datetime.fromtimestamp(0))
    response = assert_nodata_response(
        mub_client.put(f"/mub/user-service/users/{user.id}/sessions/"),
        expected_cookies={AUTH_COOKIE_NAME: str},
        expected_headers={
            "X-Session-ID": int,
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-Cookie": AUTH_COOKIE_NAME,
            "X-Session-Token": str,
        },
    )

    async with active_session():
        session = await assert_session_from_cookie(response)
        assert_contains(
            {
                "is_mub": session.is_mub,
                "user_id": session.user_id,
                "is_invalid": session.is_invalid,
                "id": session.id,
                "token": session.token,
            },
            {
                "is_mub": True,
                "user_id": user.id,
                "is_invalid": False,
                "id": int(response.headers["X-Session-ID"]),
                "token": response.headers["X-Session-Token"],
            },
        )


@pytest.mark.anyio()
async def test_upserting_disabled_mub_session(
    active_session: ActiveSession,
    session_factory: Factory[Session],
    mub_client: TestClient,
    user: User,
) -> None:
    await session_factory(is_mub=True, is_disabled=True)
    response = assert_nodata_response(
        mub_client.put(f"/mub/user-service/users/{user.id}/sessions/"),
        expected_cookies={AUTH_COOKIE_NAME: str},
        expected_headers={
            "X-Session-ID": int,
            "X-User-ID": str(user.id),
            "X-Username": user.username,
            "X-Session-Cookie": AUTH_COOKIE_NAME,
            "X-Session-Token": str,
        },
    )

    async with active_session():
        session = await assert_session_from_cookie(response)
        assert_contains(
            {
                "is_mub": session.is_mub,
                "user_id": session.user_id,
                "is_invalid": session.is_invalid,
                "id": session.id,
                "token": session.token,
            },
            {
                "is_mub": True,
                "user_id": user.id,
                "is_invalid": False,
                "id": int(response.headers["X-Session-ID"]),
                "token": response.headers["X-Session-Token"],
            },
        )


@pytest.mark.anyio()
async def test_mub_disabling_session(
    active_session: ActiveSession,
    mub_client: TestClient,
    session: Session,
    user: User,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/user-service/users/{user.id}/sessions/{session.id}/"),
    )

    async with active_session():
        assert (await get_db_session(session)).is_invalid


@pytest.mark.anyio()
async def test_mub_deleting_session(
    active_session: ActiveSession,
    mub_client: TestClient,
    session: Session,
    user: User,
) -> None:
    assert_nodata_response(
        mub_client.delete(
            f"/mub/user-service/users/{user.id}/sessions/{session.id}/",
            params={"delete_session": "true"},
        ),
    )

    async with active_session():
        assert (await Session.find_first_by_id(session.id)) is None


@pytest.mark.anyio()
async def test_authorized_method_with_mub_session(
    mub_client: TestClient,
    user: User,
    mub_session: Session,
) -> None:
    assert_response(
        mub_client.get(
            "/api/protected/user-service/users/current/home/",
            cookies={AUTH_COOKIE_NAME: mub_session.token},
        ),
        expected_json={
            "email": user.email,
            "username": user.username,
        },
    )


@pytest.mark.parametrize("method", ["POST", "PUT", "GET"])
@pytest.mark.anyio()
async def test_retrieving_mub_session_user_not_found(
    mub_client: TestClient,
    deleted_user: User,
    method: str,
) -> None:
    assert_response(
        mub_client.request(
            method, f"/mub/user-service/users/{deleted_user.id}/sessions/"
        ),
        expected_json={"detail": "User not found"},
        expected_code=404,
    )


@pytest.mark.parametrize("delete_session", [True, False])
@pytest.mark.anyio()
async def test_mub_disabling_session_user_not_found(
    mub_client: TestClient,
    session: Session,
    deleted_user: User,
    delete_session: bool,
) -> None:
    assert_response(
        mub_client.delete(
            f"/mub/user-service/users/{deleted_user.id}/sessions/{session.id}/",
            params={"delete_session": delete_session},
        ),
        expected_json={"detail": "User not found"},
        expected_code=404,
    )


@pytest.mark.parametrize("delete_session", [True, False])
@pytest.mark.anyio()
async def test_disabled_session_not_found(
    active_session: ActiveSession,
    mub_client: TestClient,
    session: Session,
    user: User,
    delete_session: bool,
) -> None:
    async with active_session():
        await session.delete()

    assert_response(
        mub_client.delete(
            f"/mub/user-service/users/{user.id}/sessions/{session.id}/",
            params={"delete_session": delete_session},
        ),
        expected_json={"detail": "Session not found"},
        expected_code=404,
    )


@pytest.mark.anyio()
async def test_listing_sessions_but_mub(
    authorized_client: TestClient,
    mub_session: Session,
) -> None:
    assert_response(
        authorized_client.get("/api/protected/user-service/sessions/"), expected_json=[]
    )


@pytest.mark.anyio()
async def test_disabling_session_mub_not_found(
    authorized_client: TestClient,
    mub_session: Session,
) -> None:
    assert_response(
        authorized_client.delete(
            f"/api/protected/user-service/sessions/{mub_session.id}"
        ),
        expected_json={"detail": "Session not found"},
        expected_code=404,
    )


@pytest.fixture()
async def mub_sessions(session_factory: Factory[Session]) -> list[Session]:
    return (
        [(await session_factory(is_mub=True)) for _ in range(3)]
        + [(await session_factory()) for _ in range(3)]
    )[::-1]


@pytest.mark.anyio()
async def test_disabling_all_other_sessions_but_mub(
    authorized_client: TestClient,
    active_session: ActiveSession,
    mub_sessions: list[Session],
) -> None:
    assert_nodata_response(
        authorized_client.delete("/api/protected/user-service/sessions/")
    )

    async with active_session():
        for session in mub_sessions:
            session = await get_db_session(session)
            assert session.is_invalid != session.is_mub


@pytest.mark.anyio()
async def test_mub_getting_all_sessions(
    mub_client: TestClient,
    user: User,
    mub_sessions: list[Session],
) -> None:
    assert_response(
        mub_client.get(f"/mub/user-service/users/{user.id}/sessions/"),
        expected_json=[
            session_checker(session, check_mub=True) for session in mub_sessions
        ],
    )


@pytest.mark.parametrize("method", ["POST", "PUT", "GET"])
@pytest.mark.anyio()
async def test_retrieving_mub_session_invalid_mub_key(
    client: TestClient,
    user: User,
    invalid_mub_key_headers: dict[str, Any] | None,
    method: str,
) -> None:
    assert_response(
        client.request(
            method,
            f"/mub/user-service/users/{user.id}/sessions/",
            headers=invalid_mub_key_headers,
        ),
        expected_json={"detail": "Invalid key"},
        expected_code=401,
    )


@pytest.mark.anyio()
async def test_mub_disabling_session_invalid_mub_key(
    client: TestClient,
    session: Session,
    user: User,
    invalid_mub_key_headers: dict[str, Any] | None,
) -> None:
    assert_response(
        client.delete(
            f"/mub/user-service/users/{user.id}/sessions/{session.id}",
            headers=invalid_mub_key_headers,
        ),
        expected_json={"detail": "Invalid key"},
        expected_code=401,
    )
