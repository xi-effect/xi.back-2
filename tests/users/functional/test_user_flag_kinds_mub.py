from collections.abc import AsyncIterator
from typing import Any

import pytest
from pydantic_marshals.base import PatchDefault, PatchDefaultType
from pytest_lazy_fixtures import lfc
from starlette import status
from starlette.testclient import TestClient

from app.users.models.user_flag_kinds_db import UserFlagKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.common.utils import repackage_json
from tests.users import factories

pytestmark = pytest.mark.anyio

USER_FLAG_KINDS_LIST_SIZE = 5


@pytest.fixture()
async def user_flag_kinds(
    active_session: ActiveSession,
) -> AsyncIterator[list[UserFlagKind]]:
    async with active_session():
        user_flag_kinds: list[UserFlagKind] = [
            await UserFlagKind.create(
                **factories.UserFlagKindInputFactory.build_python(),
            )
            for _ in range(USER_FLAG_KINDS_LIST_SIZE)
        ]

    user_flag_kinds.sort(key=lambda user_flag_kind: user_flag_kind.id)

    yield user_flag_kinds

    async with active_session():
        for user_flag_kind in user_flag_kinds:
            await user_flag_kind.delete()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, USER_FLAG_KINDS_LIST_SIZE, id="start_to_end"),
        pytest.param(
            USER_FLAG_KINDS_LIST_SIZE // 2,
            USER_FLAG_KINDS_LIST_SIZE,
            id="middle_to_end",
        ),
        pytest.param(0, USER_FLAG_KINDS_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_user_flag_kinds_listing(
    mub_client: TestClient,
    user_flag_kinds: list[UserFlagKind],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            "/mub/user-service/user-flag-kinds/",
            params={"offset": offset, "limit": limit},
        ),
        expected_json=[
            repackage_json(UserFlagKind.ResponseSchema, user_flag_kind)
            for user_flag_kind in user_flag_kinds[offset : offset + limit]
        ],
    )


async def test_user_flag_kind_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
) -> None:
    user_flag_kind_input_data: AnyJSON = factories.UserFlagKindInputFactory.build_json()

    user_flag_kind_id: int = assert_response(
        mub_client.post(
            "/mub/user-service/user-flag-kinds/",
            json=user_flag_kind_input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={**user_flag_kind_input_data, "id": int},
    ).json()["id"]

    async with active_session():
        user_flag_kind = await UserFlagKind.find_first_by_id(user_flag_kind_id)
        assert user_flag_kind is not None
        await user_flag_kind.delete()


async def test_user_flag_kind_creation_user_flag_kind_already_exists(
    mub_client: TestClient,
    other_user_flag_kind: UserFlagKind,
) -> None:
    assert_response(
        mub_client.post(
            "/mub/user-service/user-flag-kinds/",
            json=factories.UserFlagKindInputFactory.build_json(
                key=other_user_flag_kind.key,
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "User flag kind already exists"},
    )


async def test_user_flag_kind_retrieving(
    mub_client: TestClient,
    user_flag_kind: UserFlagKind,
    user_flag_kind_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/user-service/user-flag-kinds/{user_flag_kind.id}/"),
        expected_json=user_flag_kind_data,
    )


async def test_user_flag_kind_updating(
    mub_client: TestClient,
    user_flag_kind: UserFlagKind,
    user_flag_kind_data: AnyJSON,
) -> None:
    user_flag_kind_patch_data: AnyJSON = factories.UserFlagKindPatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/user-service/user-flag-kinds/{user_flag_kind.id}/",
            json=user_flag_kind_patch_data,
        ),
        expected_json={**user_flag_kind_data, **user_flag_kind_patch_data},
    )


@pytest.mark.parametrize(
    "key",
    [
        pytest.param(PatchDefault, id="key_omitted"),
        pytest.param(
            lfc(lambda user_flag_kind: user_flag_kind.key), id="key_unchanged"
        ),
    ],
)
async def test_user_flag_kind_updating_with_unchanged_key(
    mub_client: TestClient,
    user_flag_kind: UserFlagKind,
    user_flag_kind_data: AnyJSON,
    key: str | PatchDefaultType,
) -> None:
    user_flag_kind_patch_data: AnyJSON = factories.UserFlagKindPatchFactory.build_json(
        key=key,
    )

    assert_response(
        mub_client.patch(
            f"/mub/user-service/user-flag-kinds/{user_flag_kind.id}/",
            json=user_flag_kind_patch_data,
        ),
        expected_json={**user_flag_kind_data, **user_flag_kind_patch_data},
    )


async def test_user_flag_kind_updating_user_flag_kind_already_exists(
    mub_client: TestClient,
    user_flag_kind: UserFlagKind,
    other_user_flag_kind: UserFlagKind,
) -> None:
    assert_response(
        mub_client.patch(
            f"/mub/user-service/user-flag-kinds/{user_flag_kind.id}/",
            json=factories.UserFlagKindPatchFactory.build_json(
                key=other_user_flag_kind.key,
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "User flag kind already exists"},
    )


async def test_user_flag_kind_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    user_flag_kind: UserFlagKind,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/user-service/user-flag-kinds/{user_flag_kind.id}/"),
    )

    async with active_session():
        assert await UserFlagKind.find_first_by_id(user_flag_kind.id) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="retrieve"),
        pytest.param("PATCH", factories.UserFlagKindPatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_user_flag_kind_not_finding(
    mub_client: TestClient,
    deleted_user_flag_kind_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/user-service/user-flag-kinds/{deleted_user_flag_kind_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "User flag kind not found"},
    )
