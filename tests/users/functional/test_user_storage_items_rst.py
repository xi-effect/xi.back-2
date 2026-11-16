import json

import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.users.models.user_storage_items_db import UserStorageItem
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.users import factories

pytestmark = pytest.mark.anyio


async def test_user_storage_item_retrieving(
    authorized_client: TestClient,
    user_storage_item: UserStorageItem,
    user_storage_item_data: AnyJSON,
) -> None:
    assert_response(
        authorized_client.get(
            f"/api/protected/user-service/users/current/storage-items/{user_storage_item.key}/",
        ),
        expected_json=user_storage_item_data,
    )


@pytest.mark.parametrize(
    "key",
    [
        pytest.param(
            lf("deleted_user_storage_item_key"),
            id="no_existing_user_storage_item",
        ),
        pytest.param(
            lf("user_storage_item.key"),
            id="existing_user_storage_item",
        ),
    ],
)
async def test_user_storage_item_upserting(
    active_session: ActiveSession,
    user_proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    key: str,
) -> None:
    user_storage_item_put_data: AnyJSON = (
        factories.UserStorageItemValueFactory.build_json()
    )

    assert_response(
        authorized_client.put(
            f"/api/protected/user-service/users/current/storage-items/{key}/",
            json=user_storage_item_put_data,
        ),
        expected_json=user_storage_item_put_data,
    )

    async with active_session():
        user_storage_item = await UserStorageItem.find_first_by_primary_key(
            user_id=user_proxy_auth_data.user_id,
            key=key,
        )
        assert user_storage_item is not None
        assert_contains(
            json.dumps(user_storage_item.value),
            json.dumps(user_storage_item_put_data["value"]),
        )


async def test_user_storage_item_upserting_value_too_large(
    faker: Faker,
    authorized_client: TestClient,
    deleted_user_storage_item_key: str,
) -> None:
    assert_response(
        authorized_client.put(
            f"/api/protected/user-service/users/current/storage-items/{deleted_user_storage_item_key}/",
            json={
                "value": faker.pystr(
                    min_chars=UserStorageItem.max_value_size_bytes,
                    max_chars=UserStorageItem.max_value_size_bytes,
                ),
            },
        ),
        expected_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        expected_json={"detail": "User storage item value too large"},
    )


async def test_user_storage_item_deleting(
    active_session: ActiveSession,
    user_proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    user_storage_item: UserStorageItem,
) -> None:
    assert_nodata_response(
        authorized_client.delete(
            f"/api/protected/user-service/users/current/storage-items/{user_storage_item.key}/",
        ),
    )

    async with active_session():
        assert (
            await UserStorageItem.find_first_by_primary_key(
                user_id=user_proxy_auth_data.user_id,
                key=user_storage_item.key,
            )
            is None
        )


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("GET", id="retrieve"),
        pytest.param("DELETE", id="delete"),
    ],
)
async def test_user_storage_item_not_finding(
    authorized_client: TestClient,
    deleted_user_storage_item_key: str,
    method: str,
) -> None:
    assert_response(
        authorized_client.request(
            method,
            f"/api/protected/user-service/users/current/storage-items/{deleted_user_storage_item_key}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "User storage item not found"},
    )
