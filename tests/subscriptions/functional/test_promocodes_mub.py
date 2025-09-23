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
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio


@freeze_time()
@pytest.mark.parametrize(
    "body_factory",
    [
        pytest.param(factories.LimitedPromocodeInputFactory, id="limited_promocode"),
        pytest.param(
            factories.UnlimitedPromocodeInputFactory, id="unlimited_promocode"
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
            "/mub/subscription-service/promocodes/",
            json=promocode_input_data,
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
        pytest.param("by-id", lf("promocode.id"), id="promocode_by_id"),
        pytest.param("by-code", lf("promocode.code"), id="promocode_by_code"),
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
        pytest.param(
            factories.LimitedPromocodeInputFactory, id="promocode_input_factory"
        ),
        pytest.param(
            factories.UnlimitedPromocodeInputFactory,
            id="unlimited_promocode_input_factory",
        ),
    ],
)
@freeze_time()
async def test_promocode_updating(
    mub_client: TestClient,
    promocode: Promocode,
    promocode_data: AnyJSON,
    body_factory: type[BaseModelFactory[Any]],
) -> None:
    promocode_put_data = body_factory.build_json()

    assert_response(
        mub_client.put(
            f"/mub/subscription-service/promocodes/{promocode.id}/",
            json=promocode_put_data,
        ),
        expected_json={
            **promocode_data,
            **promocode_put_data,
            "updated_at": datetime_utc_now(),
        },
    )


async def test_promocode_deleting(
    active_session: ActiveSession, mub_client: TestClient, promocode: Promocode
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/subscription-service/promocodes/{promocode.id}/"),
    )

    async with active_session():
        assert await Promocode.find_first_by_id(promocode.id) is None


@pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param("POST", "", id="create_promocode"),
        pytest.param(
            "PUT", lfc(lambda promocode: f"{promocode.id}/"), id="update_promocode"
        ),
    ],
)
async def test_promocode_requesting_invalid_period(
    mub_client: TestClient, method: str, path: str
) -> None:
    promocode_input_data: AnyJSON = (
        factories.InvalidPeriodPromocodeInputFactory.build_json()
    )

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
        pytest.param(
            "POST", "", factories.LimitedPromocodeInputFactory, id="create_promocode"
        ),
        pytest.param(
            "PUT",
            lfc(lambda promocode: f"{promocode.id}/"),
            factories.LimitedPromocodeInputFactory,
            id="update_promocode",
        ),
    ],
)
async def test_promocode_requesting_already_exist(
    mub_client: TestClient,
    other_promocode: Promocode,
    method: str,
    path: str,
    body_factory: type[BaseModelFactory[Any]],
) -> None:
    promocode_put_data = body_factory.build_json(code=other_promocode.code)

    assert_response(
        mub_client.request(
            method,
            f"/mub/subscription-service/promocodes/{path}",
            json=promocode_put_data,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode already exists"},
    )


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
    ("method", "path", "body_factory"),
    [
        pytest.param("PUT", factories.LimitedPromocodeInputFactory, id="put"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_promocode_not_finding(
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
