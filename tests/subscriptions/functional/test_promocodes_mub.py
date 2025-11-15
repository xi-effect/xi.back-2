from typing import Any

import pytest
from freezegun import freeze_time
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.subscriptions.factories import (
    InvalidPromocodePeriodInputFactory,
    PromocodeInputFactory,
    UnlimitedPromocodeInputFactory,
)

pytestmark = pytest.mark.anyio


@freeze_time()
@pytest.mark.parametrize(
    "body_factory",
    [
        pytest.param(PromocodeInputFactory, id="promocode_input_factory"),
        pytest.param(
            UnlimitedPromocodeInputFactory, id="unlimited_promocode_input_factory"
        ),
    ],
)
async def test_promocode_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
    body_factory: type[BaseModelFactory[Any]],
) -> None:
    promocode_input_data: AnyJSON = body_factory.build_json()

    promocode_id: int = assert_response(
        mub_client.post(
            "/mub/subscription-service/promocodes/", json=promocode_input_data
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **promocode_input_data,
            "id": int,
            "created_at": datetime_utc_now(),
            "updated_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        promocode = await Promocode.find_first_by_id(promocode_id)
        assert promocode is not None
        await promocode.delete()


@pytest.mark.parametrize(
    ("path", "field_by"),
    [
        pytest.param("by-id", lf("promocode_id"), id="promocode_by_id"),
        pytest.param(
            "by-code", lfc(lambda promocode: promocode.code), id="promocode_by_code"
        ),
    ],
)
async def test_promocode_retrieving(
    mub_client: TestClient, promocode_data: AnyJSON, path: str, field_by: str
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/subscription-service/promocodes/{path}/{field_by}/",
        ),
        expected_json=promocode_data,
    )


@pytest.mark.parametrize(
    "body_factory",
    [
        pytest.param(PromocodeInputFactory, id="promocode_input_factory"),
        pytest.param(
            UnlimitedPromocodeInputFactory, id="unlimited_promocode_input_factory"
        ),
    ],
)
@freeze_time()
async def test_promocode_updating(
    mub_client: TestClient,
    promocode_id: int,
    promocode_data: AnyJSON,
    body_factory: type[BaseModelFactory[Any]],
) -> None:
    promocode_put_data = body_factory.build_json()

    assert_response(
        mub_client.put(
            f"/mub/subscription-service/promocodes/{promocode_id}/",
            json=promocode_put_data,
        ),
        expected_json={
            **promocode_data,
            **promocode_put_data,
            "updated_at": datetime_utc_now(),
        },
    )


@freeze_time()
async def test_promocode_update_keeps_code(
    mub_client: TestClient,
    promocode_id: int,
    promocode_data: AnyJSON,
) -> None:
    promocode_put_data = PromocodeInputFactory.build_json(code=promocode_data["code"])

    assert_response(
        mub_client.put(
            f"/mub/subscription-service/promocodes/{promocode_id}/",
            json=promocode_put_data,
        ),
        expected_json={
            **promocode_data,
            **promocode_put_data,
            "updated_at": datetime_utc_now(),
        },
    )


async def test_promocode_deleting(
    active_session: ActiveSession, mub_client: TestClient, promocode_id: int
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/subscription-service/promocodes/{promocode_id}/"),
    )

    async with active_session():
        assert await Promocode.find_first_by_id(promocode_id) is None


@pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param("POST", "", id="create_promocode"),
        pytest.param(
            "PUT", lfc(lambda promocode_id: f"{promocode_id}/"), id="update_promocode"
        ),
    ],
)
async def test_promocode_requesting_invalid_period(
    mub_client: TestClient, method: str, path: str
) -> None:
    promocode_input_data: AnyJSON = InvalidPromocodePeriodInputFactory.build_json()

    assert_response(
        mub_client.request(
            method,
            f"/mub/subscription-service/promocodes/{path}",
            json=promocode_input_data,
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body"],
                    "msg": "Value error, the end date cannot be earlier than the start date",
                }
            ]
        },
    )


@pytest.mark.parametrize(
    ("method", "path", "body_factory"),
    [
        pytest.param("POST", "", PromocodeInputFactory, id="create_promocode"),
        pytest.param(
            "POST", "", UnlimitedPromocodeInputFactory, id="create_unlimited_promocode"
        ),
        pytest.param(
            "PUT",
            lfc(lambda promocode_id: f"{promocode_id}/"),
            PromocodeInputFactory,
            id="update_promocode",
        ),
        pytest.param(
            "PUT",
            lfc(lambda promocode_id: f"{promocode_id}/"),
            UnlimitedPromocodeInputFactory,
            id="update_unlimited_promocode",
        ),
    ],
)
@freeze_time()
async def test_promocode_requesting_exist_code(
    active_session: ActiveSession,
    mub_client: TestClient,
    method: str,
    path: str,
    body_factory: type[BaseModelFactory[Any]],
) -> None:
    promocode_put_data = body_factory.build_json()
    async with active_session():
        existing_promocode: Promocode = await Promocode.create(**promocode_put_data)

    assert_response(
        mub_client.request(
            method,
            f"/mub/subscription-service/promocodes/{path}",
            json=promocode_put_data,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode already exists"},
    )

    async with active_session():
        await existing_promocode.delete()


@pytest.mark.parametrize(
    ("path", "deleted_field"),
    [
        pytest.param("by-id", lf("deleted_promocode_id"), id="promocode_by_id"),
        pytest.param("by-code", lf("deleted_promocode_code"), id="promocode_by_code"),
    ],
)
async def test_promocode_retrieving_not_finding(
    mub_client: TestClient, path: str, deleted_field: str
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/subscription-service/promocodes/{path}/{deleted_field}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Promocode not found"},
    )


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("PUT", PromocodeInputFactory, id="put"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_promocodes_not_finding(
    mub_client: TestClient,
    deleted_promocode_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/subscription-service/promocodes/{deleted_promocode_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Promocode not found"},
    )
