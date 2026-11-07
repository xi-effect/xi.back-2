from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.users.models.user_flag_kinds_db import UserFlagKind
from app.users.models.user_flags_db import UserFlag
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.users import factories

pytestmark = pytest.mark.anyio


async def test_user_flag_retrieving_default_value(
    authorized_client: TestClient,
    user_flag_kind: UserFlagKind,
) -> None:
    assert_response(
        authorized_client.get(
            f"/api/protected/user-service/users/current/flags/{user_flag_kind.key}/",
        ),
        expected_json={"value": user_flag_kind.default_value},
    )


async def test_user_flag_retrieving_stored_value(
    authorized_client: TestClient,
    user_flag_kind: UserFlagKind,
    user_flag: UserFlag,
) -> None:
    assert_response(
        authorized_client.get(
            f"/api/protected/user-service/users/current/flags/{user_flag_kind.key}/",
        ),
        expected_json={"value": user_flag.value},
    )


@pytest.mark.parametrize(
    "existing_user_flag",
    [
        pytest.param(None, id="no_existing_user_flag"),
        pytest.param(lf("user_flag"), id="existing_user_flag"),
    ],
)
async def test_user_flag_upserting(
    active_session: ActiveSession,
    user_proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    user_flag_kind: UserFlagKind,
    existing_user_flag: UserFlag | None,
) -> None:
    user_flag_put_data: AnyJSON = factories.UserFlagValueFactory.build_json()

    assert_response(
        authorized_client.put(
            f"/api/protected/user-service/users/current/flags/{user_flag_kind.key}/",
            json=user_flag_put_data,
        ),
        expected_json=user_flag_put_data,
    )

    async with active_session():
        user_flag = await UserFlag.find_first_by_primary_key(
            user_id=user_proxy_auth_data.user_id,
            user_flag_kind_id=user_flag_kind.id,
        )
        assert user_flag is not None
        assert_contains(user_flag, user_flag_put_data)

        await UserFlag.delete_by_kwargs(
            user_id=user_proxy_auth_data.user_id,
            user_flag_kind_id=user_flag_kind.id,
        )


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="retrieve"),
        pytest.param("PUT", factories.UserFlagValueFactory, id="upsert"),
    ],
)
async def test_user_flag_kind_not_finding(
    authorized_client: TestClient,
    deleted_user_flag_kind_key: str,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        authorized_client.request(
            method,
            f"/api/protected/user-service/users/current/flags/{deleted_user_flag_kind_key}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "User flag kind not found"},
    )
