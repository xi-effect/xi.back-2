from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from faker import Faker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.schemas.subscriptions_sch import PaidPlanKind
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.promocode_redemptions_db import PromocodeRedemption
from app.subscriptions.models.promocodes_db import Promocode
from app.subscriptions.models.subscriptions_db import Subscription
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.factories import DetailedUserFactory
from tests.subscriptions import factories
from tests.subscriptions.conftest import subscription_extension_parametrization

pytestmark = pytest.mark.anyio


@subscription_extension_parametrization
@freeze_time()
async def test_promocode_redemption(
    faker: Faker,
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
    existing_subscription: Subscription | None,
    subscription_extended_from: datetime | None,
) -> None:
    promocode_settings = factories.AccountAgePromocodeSettingsFactory.build()
    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **promocode_settings.model_dump(),
            }
        )

    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{authorized_user_id}/"
    ).respond(
        json=DetailedUserFactory.build_json(
            created_at=faker.date_time_between(
                start_date=datetime_utc_now()
                - timedelta(days=promocode_settings.max_account_age_days),
                tzinfo=timezone.utc,
            )
        )
    )

    assert_nodata_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{promocode.code}/redemptions/",
        ),
    )

    async with active_session():
        assert_contains(
            await PromocodeRedemption.find_first_by_kwargs(
                promocode_id=promocode.id, user_id=authorized_user_id
            ),
            {"created_at": datetime_utc_now()},
        )

        updated_promocode = await Promocode.find_first_by_id(promocode.id)
        assert updated_promocode is not None
        assert_contains(updated_promocode, {"usage_count": promocode.usage_count + 1})

        subscription = await Subscription.find_first_by_id(authorized_user_id)
        assert subscription is not None
        assert_contains(
            subscription,
            {
                "plan_kind": PaidPlanKind.PRO,
                "ends_at": (subscription_extended_from or datetime_utc_now())
                + timedelta(days=promocode.subscription_days),
            },
        )

        await updated_promocode.delete()
        if existing_subscription is None:
            await subscription.delete()

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_promocode_redemption_promocode_already_redeemed(
    active_session: ActiveSession,
    authorized_user_id: int,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **factories.UnrestrictedPromocodeSettingsFactory.build_python(),
            }
        )
        await PromocodeRedemption.create(
            promocode_id=promocode.id, user_id=authorized_user_id
        )

    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode already redeemed"},
    )

    async with active_session():
        await promocode.delete()


@pytest.mark.parametrize(
    ("settings_factory", "error"),
    [
        pytest.param(
            factories.FuturePeriodPromocodeSettingsFactory,
            "Promocode not active yet",
            id="future_validity_period",
        ),
        pytest.param(
            factories.PastPeriodPromocodeSettingsFactory,
            "Promocode expired",
            id="past_validity_period",
        ),
    ],
)
async def test_promocode_redemption_outside_validity_period(
    active_session: ActiveSession,
    authorized_user_id: int,
    authorized_client: TestClient,
    settings_factory: type[BaseModelFactory[Any]],
    error: str,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **settings_factory.build_python(),
            }
        )

    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": error},
    )

    async with active_session():
        assert (
            await PromocodeRedemption.find_first_by_kwargs(
                promocode_id=promocode.id, user_id=authorized_user_id
            )
            is None
        )

        await promocode.delete()


async def test_promocode_redemption_promocode_max_account_age_exceeded(
    faker: Faker,
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
) -> None:
    promocode_settings = factories.AccountAgePromocodeSettingsFactory.build()
    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **promocode_settings.model_dump(),
            }
        )

    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{authorized_user_id}/"
    ).respond(
        json=DetailedUserFactory.build_json(
            created_at=faker.date_time_between(
                end_date=datetime_utc_now()
                - timedelta(days=promocode_settings.max_account_age_days),
                tzinfo=timezone.utc,
            )
        )
    )

    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode max account age exceeded"},
    )

    async with active_session():
        assert (
            await PromocodeRedemption.find_first_by_kwargs(
                promocode_id=promocode.id, user_id=authorized_user_id
            )
            is None
        )

        await promocode.delete()

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_promocode_redemption_promocode_usage_limit_reached(
    faker: Faker,
    active_session: ActiveSession,
    authorized_user_id: int,
    authorized_client: TestClient,
) -> None:
    usage_count: int = faker.pyint(min_value=1, max_value=100)

    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **factories.UnrestrictedPromocodeSettingsFactory.build_python(),
                "usage_count": usage_count,
                "usage_limit": faker.pyint(min_value=1, max_value=usage_count),
            }
        )

    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode usage limit reached"},
    )

    async with active_session():
        assert (
            await PromocodeRedemption.find_first_by_kwargs(
                promocode_id=promocode.id, user_id=authorized_user_id
            )
            is None
        )

        await promocode.delete()


async def test_promocode_redemption_promocode_not_found(
    authorized_client: TestClient,
    deleted_promocode: Promocode,
) -> None:
    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{deleted_promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Promocode not found"},
    )
