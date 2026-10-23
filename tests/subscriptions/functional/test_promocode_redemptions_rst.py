from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest
from faker import Faker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.schemas.subscriptions_sch import PaidPlanKind, UserPlanUpdateEventSchema
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
from tests.subscriptions.conftest import existing_subscription_parametrization

pytestmark = pytest.mark.anyio


@existing_subscription_parametrization
@pytest.mark.parametrize(
    "is_account_age_limited",
    [
        pytest.param(False, id="account_age_not_limited"),
        pytest.param(True, id="account_age_limited"),
    ],
)
@freeze_time()
async def test_promocode_redemption(
    faker: Faker,
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
    publish_user_plan_update_mock: AsyncMock,
    redeemable_promocode: Promocode,
    existing_subscription: Subscription | None,
    subscription_extended_from: datetime | None,
    is_account_age_limited: bool,
) -> None:
    if is_account_age_limited:
        max_account_age_days: int = faker.pyint(min_value=1, max_value=365)
        async with active_session() as session:
            session.add(redeemable_promocode)
            redeemable_promocode.update(max_account_age_days=max_account_age_days)

        users_internal_bridge_mock = users_internal_respx_mock.get(
            path=f"/users/{authorized_user_id}/"
        ).respond(
            json=DetailedUserFactory.build_json(
                created_at=faker.date_time_between(
                    start_date=datetime_utc_now()
                    - timedelta(days=max_account_age_days),
                    tzinfo=timezone.utc,
                )
            )
        )

    assert_nodata_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{redeemable_promocode.code}/redemptions/",
        ),
    )

    async with active_session():
        assert_contains(
            await PromocodeRedemption.find_first_by_kwargs(
                promocode_id=redeemable_promocode.id,
                user_id=authorized_user_id,
            ),
            {"created_at": datetime_utc_now()},
        )
        assert_contains(
            await Promocode.find_first_by_id(redeemable_promocode.id),
            {"usage_count": redeemable_promocode.usage_count + 1},
        )

        subscription = await Subscription.find_first_by_id(authorized_user_id)
        assert subscription is not None
        assert_contains(
            subscription,
            {
                "plan_kind": PaidPlanKind.PRO,
                "ends_at": (subscription_extended_from or datetime_utc_now())
                + timedelta(days=redeemable_promocode.subscription_days),
            },
        )
        if existing_subscription is None:
            await subscription.delete()

    if is_account_age_limited:
        assert_last_httpx_request(
            users_internal_bridge_mock,
            expected_headers={"X-Api-Key": settings.api_key},
        )
    else:
        users_internal_respx_mock.calls.assert_not_called()

    publish_user_plan_update_mock.assert_awaited_once_with(
        UserPlanUpdateEventSchema(user_id=authorized_user_id)
    )


async def test_promocode_redemption_promocode_usage_limit_reached(
    faker: Faker,
    active_session: ActiveSession,
    authorized_client: TestClient,
    redeemable_promocode: Promocode,
) -> None:
    usage_limit: int = faker.pyint(min_value=1)
    async with active_session() as session:
        session.add(redeemable_promocode)
        redeemable_promocode.update(usage_limit=usage_limit, usage_count=usage_limit)

    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{redeemable_promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode usage limit reached"},
    )


async def test_promocode_redemption_promocode_max_account_age_exceeded(
    faker: Faker,
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
    redeemable_promocode: Promocode,
) -> None:
    max_account_age_days: int = faker.pyint(min_value=1, max_value=365)
    async with active_session() as session:
        session.add(redeemable_promocode)
        redeemable_promocode.update(max_account_age_days=max_account_age_days)

    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{authorized_user_id}/"
    ).respond(
        json=DetailedUserFactory.build_json(
            created_at=faker.date_time_between(
                end_date=datetime_utc_now() - timedelta(days=max_account_age_days),
                tzinfo=timezone.utc,
            )
        )
    )

    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{redeemable_promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode max account age exceeded"},
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


@pytest.mark.parametrize(
    ("settings_factory", "error"),
    [
        pytest.param(
            factories.FuturePeriodPromocodeSettingsFactory,
            "Promocode not active yet",
            id="promocode_not_active_yet",
        ),
        pytest.param(
            factories.PastPeriodPromocodeSettingsFactory,
            "Promocode expired",
            id="promocode_expired",
        ),
    ],
)
async def test_promocode_redemption_outside_validity_period(
    active_session: ActiveSession,
    authorized_client: TestClient,
    redeemable_promocode: Promocode,
    settings_factory: type[BaseModelFactory[Any]],
    error: str,
) -> None:
    async with active_session() as session:
        session.add(redeemable_promocode)
        redeemable_promocode.update(**settings_factory.build_python())

    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{redeemable_promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": error},
    )


async def test_promocode_redemption_promocode_already_redeemed(
    active_session: ActiveSession,
    authorized_user_id: int,
    authorized_client: TestClient,
    redeemable_promocode: Promocode,
) -> None:
    async with active_session():
        await PromocodeRedemption.create(
            promocode_id=redeemable_promocode.id,
            user_id=authorized_user_id,
        )

    assert_response(
        authorized_client.post(
            f"/api/protected/subscription-service/promocodes/{redeemable_promocode.code}/redemptions/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode already redeemed"},
    )


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
