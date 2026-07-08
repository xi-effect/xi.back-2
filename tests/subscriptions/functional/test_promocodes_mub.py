from typing import Any

import pytest
from faker import Faker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.promocodes_db import Promocode
from app.subscriptions.routes.promocodes_mub import (
    PromocodeBatchGenerationRequestSchema,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import (
    assert_nodata_response,
    assert_response,
)
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio

promocode_validity_period_factory_parametrization = pytest.mark.parametrize(
    "validity_period_factory",
    [
        pytest.param(
            factories.LimitedPromocodeValidityPeriodInputFactory,
            id="limited_validity_period",
        ),
        pytest.param(
            factories.UnlimitedPromocodeValidityPeriodInputFactory,
            id="unlimited_validity_period",
        ),
    ],
)


@promocode_validity_period_factory_parametrization
@freeze_time()
async def test_promocode_batch_generation(
    faker: Faker,
    active_session: ActiveSession,
    mub_client: TestClient,
    validity_period_factory: type[BaseModelFactory[Any]],
) -> None:
    data: PromocodeBatchGenerationRequestSchema = (
        factories.PromocodeBatchGenerationRequestFactory.build(
            validity_period=validity_period_factory.build()
        )
    )

    response_json: list[str] = assert_response(
        mub_client.post(
            "/mub/subscription-service/promocode-batch-generation-requests/",
            json=data.model_dump(mode="json"),
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json=[str for _ in range(data.batch_size)],
    ).json()

    async with active_session():
        for index, code in enumerate(response_json):
            promocode = await Promocode.find_first_by_kwargs(code=code)
            assert promocode is not None
            assert_contains(
                promocode,
                {
                    **data.validity_period.model_dump(),
                    "id": int,
                    "title": data.title_template.format(index=index),
                    "created_at": datetime_utc_now(),
                    "updated_at": datetime_utc_now(),
                },
            )
            await promocode.delete()


async def test_promocode_batch_generation_invalid_period(
    mub_client: TestClient,
) -> None:
    assert_response(
        mub_client.post(
            "/mub/subscription-service/promocode-batch-generation-requests/",
            json=factories.PromocodeBatchGenerationRequestFactory.build_json(
                factory_use_construct=True,
                validity_period=factories.InvalidPromocodeValidityPeriodInputFactory.build(),
            ),
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body", "validity_period"],
                    "msg": "Value error, the end date cannot be earlier than the start date",
                }
            ]
        },
    )


@promocode_validity_period_factory_parametrization
@freeze_time()
async def test_promocode_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
    validity_period_factory: type[BaseModelFactory[Any]],
) -> None:
    promocode_input_data: AnyJSON = factories.PromocodeWithCodeInputFactory.build_json()
    validity_period_data: AnyJSON = validity_period_factory.build_json()

    promocode_id: int = assert_response(
        mub_client.post(
            "/mub/subscription-service/promocodes/",
            json={
                **promocode_input_data,
                **validity_period_data,
            },
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **promocode_input_data,
            **validity_period_data,
            "id": int,
            "created_at": datetime_utc_now(),
            "updated_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        promocode = await Promocode.find_first_by_id(promocode_id)
        assert promocode is not None
        await promocode.delete()


@promocode_validity_period_factory_parametrization
@freeze_time()
async def test_promocode_creation_with_generated_code(
    active_session: ActiveSession,
    mub_client: TestClient,
    validity_period_factory: type[BaseModelFactory[Any]],
) -> None:
    promocode_input_data: AnyJSON = factories.PromocodeNoCodeInputFactory.build_json()
    validity_period_data: AnyJSON = validity_period_factory.build_json()

    promocode_data: AnyJSON = assert_response(
        mub_client.post(
            "/mub/subscription-service/promocodes/",
            json={
                **promocode_input_data,
                **validity_period_data,
            },
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **promocode_input_data,
            **validity_period_data,
            "id": int,
            "code": str,
            "created_at": datetime_utc_now(),
            "updated_at": datetime_utc_now(),
        },
    ).json()

    async with active_session():
        promocode = await Promocode.find_first_by_id(promocode_data["id"])
        assert promocode is not None
        assert_contains(promocode, {"code": promocode_data["code"]})
        await promocode.delete()


async def test_promocode_creation_invalid_period(
    mub_client: TestClient,
) -> None:
    assert_response(
        mub_client.post(
            "/mub/subscription-service/promocodes/",
            json={
                **factories.PromocodeWithCodeInputFactory.build_json(),
                **factories.InvalidPromocodeValidityPeriodInputFactory.build_json(),
            },
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
            json={
                **factories.PromocodeNoCodeInputFactory.build_json(),
                **factories.LimitedPromocodeValidityPeriodInputFactory.build_json(),
                "code": other_promocode.code,
            },
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


@promocode_validity_period_factory_parametrization
@freeze_time()
async def test_promocode_updating(
    mub_client: TestClient,
    promocode: Promocode,
    promocode_data: AnyJSON,
    validity_period_factory: type[BaseModelFactory[Any]],
) -> None:
    promocode_put_data: AnyJSON = factories.PromocodeUpdateFactory.build_json()
    validity_period_data: AnyJSON = validity_period_factory.build_json()

    assert_response(
        mub_client.put(
            f"/mub/subscription-service/promocodes/{promocode.id}/",
            json={
                **promocode_put_data,
                **validity_period_data,
            },
        ),
        expected_json={
            **promocode_data,
            **promocode_put_data,
            **validity_period_data,
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
            json={
                **factories.PromocodeUpdateFactory.build_json(),
                **factories.InvalidPromocodeValidityPeriodInputFactory.build_json(),
            },
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
            json={
                **factories.PromocodeUpdateFactory.build_json(),
                **factories.LimitedPromocodeValidityPeriodInputFactory.build_json(),
                "code": other_promocode.code,
            },
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
    ("method", "path", "body_factory"),
    [
        pytest.param(
            "GET",
            lfc(lambda deleted_promocode: f"by-id/{deleted_promocode.id}/"),
            None,
            id="retrieve_by_id",
        ),
        pytest.param(
            "GET",
            lfc(lambda deleted_promocode: f"by-code/{deleted_promocode.code}/"),
            None,
            id="retrieve_by_code",
        ),
        pytest.param(
            "PUT",
            lfc(lambda deleted_promocode: f"{deleted_promocode.id}/"),
            factories.PromocodeNoCodeInputFactory,
            id="put",
        ),
        pytest.param(
            "DELETE",
            lfc(lambda deleted_promocode: f"{deleted_promocode.id}/"),
            None,
            id="delete",
        ),
    ],
)
async def test_promocode_not_finding(
    mub_client: TestClient,
    method: str,
    path: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/subscription-service/promocodes/{path}",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Promocode not found"},
    )
