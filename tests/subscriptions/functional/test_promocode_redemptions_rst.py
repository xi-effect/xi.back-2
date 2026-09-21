from datetime import datetime, timedelta
from typing import Any, Literal

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.promocode_redemptions_db import PromocodeRedemption
from app.subscriptions.models.promocodes_db import Promocode
from app.subscriptions.models.subscriptions_db import Subscription, SubscriptionPlanKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.factories import DetailedUserFactory
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio


async def assert_promocode_redeemed(
    authorized_user_id: int,
    promocode: Promocode,
    expected_ends_at: datetime,
) -> Subscription:
    subscription = await Subscription.find_active_by_user_id(user_id=authorized_user_id)
    assert subscription is not None
    assert_contains(
        subscription,
        {
            "plan_kind": SubscriptionPlanKind.PRO,
            "ends_at": expected_ends_at,
        },
    )

    updated_promocode = await Promocode.find_first_by_id(promocode.id)
    assert updated_promocode is not None
    assert_contains(updated_promocode, {"usage_count": promocode.usage_count + 1})

    promocode_redemption = await PromocodeRedemption.find_first_by_kwargs(
        promocode_id=promocode.id, user_id=authorized_user_id
    )
    assert promocode_redemption is not None
    assert_contains(promocode_redemption, {"created_at": datetime_utc_now()})

    return subscription


@pytest.mark.parametrize(
    ("subscription_state", "max_account_age_days", "promocode_factory"),
    [
        pytest.param(
            None,
            None,
            factories.UnrestrictedPromocodeInputFactory,
            id="no_subscription-no_restriction",
        ),
        pytest.param(
            None,
            30,
            factories.UnrestrictedPromocodeInputFactory,
            id="no_subscription-with_restriction",
        ),
        pytest.param(
            "active",
            None,
            factories.UnrestrictedPromocodeInputFactory,
            id="active_subscription-no_restriction",
        ),
        pytest.param(
            "active",
            30,
            factories.UnrestrictedPromocodeInputFactory,
            id="active_subscription-with_restriction",
        ),
        pytest.param(
            "expired",
            None,
            factories.UnrestrictedPromocodeInputFactory,
            id="expired_subscription-no_restriction",
        ),
        pytest.param(
            "expired",
            30,
            factories.UnrestrictedPromocodeInputFactory,
            id="expired_subscription-with_restriction",
        ),
        pytest.param(
            None,
            None,
            factories.RedeemablePromocodeInputFactory,
            id="no_subscription-no_restriction-satisfied_promocode_restrictions",
        ),
    ],
)
@freeze_time()
async def test_promocode_redemption(
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
    subscription_state: Literal["active", "expired"] | None,
    max_account_age_days: int | None,
    promocode_factory: type[BaseModelFactory[Promocode.InputSchema]],
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **promocode_factory.build_python(
                max_account_age_days=max_account_age_days,
            ),
        )
        existing_subscription: Subscription | None = None
        if subscription_state == "active":
            existing_subscription = await Subscription.create(
                user_id=authorized_user_id,
                plan_kind=SubscriptionPlanKind.PRO,
                ends_at=datetime_utc_now() + timedelta(days=5),
            )
        elif subscription_state == "expired":
            existing_subscription = await Subscription.create(
                user_id=authorized_user_id,
                plan_kind=SubscriptionPlanKind.PRO,
                ends_at=datetime_utc_now() - timedelta(days=1),
            )

    if max_account_age_days is not None:
        users_internal_bridge_mock = users_internal_respx_mock.get(
            path=f"/users/{authorized_user_id}/"
        ).respond(
            json=DetailedUserFactory.build_json(created_at=datetime_utc_now()),
        )

    assert_nodata_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": promocode.code},
        ),
    )

    async with active_session():
        if subscription_state == "active":
            assert existing_subscription is not None
            expected_ends_at = existing_subscription.ends_at + timedelta(
                days=promocode.subscription_days
            )
        else:
            expected_ends_at = datetime_utc_now() + timedelta(
                days=promocode.subscription_days
            )

        subscription = await assert_promocode_redeemed(
            authorized_user_id=authorized_user_id,
            promocode=promocode,
            expected_ends_at=expected_ends_at,
        )

        expected_row_count = 2 if subscription_state == "expired" else 1
        assert (
            await Subscription.count_by_kwargs(
                Subscription.id, user_id=authorized_user_id
            )
            == expected_row_count
        )

        if subscription_state == "active":
            assert existing_subscription is not None
            assert_contains(subscription, {"id": existing_subscription.id})
        else:
            assert_contains(subscription, {"created_at": datetime_utc_now()})
            if subscription_state == "expired":
                assert existing_subscription is not None
                assert subscription.id != existing_subscription.id
                await existing_subscription.delete()

        await subscription.delete()
        await promocode.delete()

    if max_account_age_days is None:
        users_internal_respx_mock.calls.assert_not_called()
    else:
        assert_last_httpx_request(
            users_internal_bridge_mock,
            expected_headers={"X-Api-Key": settings.api_key},
        )


async def test_promocode_redemption_promocode_not_found(
    authorized_client: TestClient,
    deleted_promocode: Promocode,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": deleted_promocode.code},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Promocode not found"},
    )


@pytest.mark.parametrize(
    ("promocode_overrides", "is_already_redeemed", "account_created_days_ago", "error"),
    [
        pytest.param(
            {"valid_from": datetime_utc_now() + timedelta(days=1)},
            False,
            None,
            "Promocode not active yet",
            id="not_active_yet",
        ),
        pytest.param(
            {"valid_until": datetime_utc_now() - timedelta(days=1)},
            False,
            None,
            "Promocode expired",
            id="expired",
        ),
        pytest.param(
            {"usage_limit": 1, "usage_count": 1},
            False,
            None,
            "Promocode usage limit reached",
            id="usage_limit_reached",
        ),
        pytest.param(
            {},
            True,
            None,
            "Promocode already redeemed",
            id="already_redeemed",
        ),
        pytest.param(
            {},
            False,
            2,
            "Promocode max account age exceeded",
            id="max_account_age_exceeded",
        ),
    ],
)
async def test_promocode_redemption_conflict(
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
    promocode_overrides: dict[str, Any],
    is_already_redeemed: bool,
    account_created_days_ago: int | None,
    error: str,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.UnrestrictedPromocodeInputFactory.build_python(
                    max_account_age_days=1,
                ),
                **promocode_overrides,
            },
        )
        if is_already_redeemed:
            await PromocodeRedemption.create(
                promocode_id=promocode.id, user_id=authorized_user_id
            )

    if account_created_days_ago is not None:
        users_internal_bridge_mock = users_internal_respx_mock.get(
            path=f"/users/{authorized_user_id}/"
        ).respond(
            json=DetailedUserFactory.build_json(
                created_at=datetime_utc_now() - timedelta(days=account_created_days_ago)
            ),
        )

    assert_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": promocode.code},
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": error},
    )

    async with active_session():
        await promocode.delete()

    if account_created_days_ago is None:
        users_internal_respx_mock.calls.assert_not_called()
    else:
        assert_last_httpx_request(
            users_internal_bridge_mock,
            expected_headers={"X-Api-Key": settings.api_key},
        )


async def test_promocode_redemption_usage_limit_reached_concurrently(
    active_session: ActiveSession,
    mock_stack: MockStack,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **factories.UnrestrictedPromocodeInputFactory.build_python(
                usage_limit=1,
            ),
        )

    mock_stack.enter_async_mock(
        Promocode, "has_incremented_usage_count_by_id", return_value=False
    )

    assert_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": promocode.code},
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode usage limit reached"},
    )

    async with active_session():
        await promocode.delete()
