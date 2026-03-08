from typing import Any

import pytest
from freezegun import freeze_time
from pytest_lazy_fixtures import lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import (
    assert_nodata_response,
    assert_response,
)
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio


promocode_body_factory_parametrization = pytest.mark.parametrize(
    "body_factory",
    [
        pytest.param(
            factories.LimitedPromocodeInputFactory,
            id="limited_promocode",
        ),
        pytest.param(
            factories.UnlimitedPromocodeInputFactory,
            id="unlimited_promocode",
        ),
    ],
)


@promocode_body_factory_parametrization
@freeze_time()
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


async def test_promocode_creation_invalid_period(
    mub_client: TestClient,
) -> None:
    assert_response(
        mub_client.post(
            "/mub/subscription-service/promocodes/",
            json=factories.InvalidPeriodPromocodeInputFactory.build_json(),
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


async def test_promocode_creation_promocode_already_exists(
    mub_client: TestClient,
    other_promocode: Promocode,
) -> None:
    assert_response(
        mub_client.post(
            "/mub/subscription-service/promocodes/",
            json=factories.LimitedPromocodeInputFactory.build_json(
                code=other_promocode.code
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode already exists"},
    )


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(
            lfc(lambda promocode: f"by-id/{promocode.id}/"),
            id="by_id",
        ),
        pytest.param(
            lfc(lambda promocode: f"by-code/{promocode.code}/"),
            id="by_code",
        ),
    ],
)
async def test_promocode_retrieving(
    mub_client: TestClient,
    promocode_data: AnyJSON,
    path: str,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/subscription-service/promocodes/{path}",
        ),
        expected_json=promocode_data,
    )


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(
            lfc(lambda deleted_promocode: f"by-id/{deleted_promocode.id}/"),
            id="by_id",
        ),
        pytest.param(
            lfc(lambda deleted_promocode: f"by-code/{deleted_promocode.code}/"),
            id="by_code",
        ),
    ],
)
async def test_promocode_retrieving_promocode_not_found(
    mub_client: TestClient,
    path: str,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/subscription-service/promocodes/{path}",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Promocode not found"},
    )


@promocode_body_factory_parametrization
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


async def test_promocode_updating_invalid_period(
    mub_client: TestClient,
    promocode: Promocode,
) -> None:
    assert_response(
        mub_client.put(
            f"/mub/subscription-service/promocodes/{promocode.id}/",
            json=factories.InvalidPeriodPromocodeInputFactory.build_json(),
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


async def test_promocode_updating_promocode_already_exists(
    mub_client: TestClient,
    promocode: Promocode,
    other_promocode: Promocode,
) -> None:
    assert_response(
        mub_client.put(
            f"/mub/subscription-service/promocodes/{promocode.id}/",
            json=factories.LimitedPromocodeInputFactory.build_json(
                code=other_promocode.code
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode already exists"},
    )


async def test_promocode_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    promocode: Promocode,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/subscription-service/promocodes/{promocode.id}/"),
    )

    async with active_session():
        assert await Promocode.find_first_by_id(promocode.id) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("PUT", factories.LimitedPromocodeInputFactory, id="put"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_promocode_not_finding(
    mub_client: TestClient,
    deleted_promocode: Promocode,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/subscription-service/promocodes/{deleted_promocode.id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Promocode not found"},
    )
