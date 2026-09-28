from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
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
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.factories import DetailedUserFactory
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("existing_subscription", "subscription_extended_from"),
    [
        pytest.param(None, None, id="no_subscription"),
        pytest.param(lf("expired_subscription"), None, id="expired_subscription"),
        pytest.param(
            lf("active_subscription"),
            lf("active_subscription.ends_at"),
            id="active_subscription",
        ),
    ],
)
@freeze_time()
async def test_promocode_redemption(
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
    existing_subscription: Subscription | None,
    subscription_extended_from: datetime | None,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **factories.UnrestrictedPromocodeInputFactory.build_python(),
        )

    current_timestamp = datetime_utc_now()

    assert_nodata_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": promocode.code},
        ),
    )

    async with active_session():
        updated_subscription = await Subscription.find_first_by_id(authorized_user_id)
        assert updated_subscription is not None
        assert_contains(
            updated_subscription,
            {
                "plan_kind": PaidPlanKind.PRO,
                "ends_at": (subscription_extended_from or current_timestamp)
                + timedelta(days=promocode.subscription_days),
            },
        )

        updated_promocode = await Promocode.find_first_by_id(promocode.id)
        assert updated_promocode is not None
        assert_contains(updated_promocode, {"usage_count": promocode.usage_count + 1})

        redemption = await PromocodeRedemption.find_first_by_kwargs(
            promocode_id=promocode.id, user_id=authorized_user_id
        )
        assert redemption is not None
        assert_contains(redemption, {"created_at": current_timestamp})

        if existing_subscription is None:
            await updated_subscription.delete()
        await updated_promocode.delete()

    users_internal_respx_mock.calls.assert_not_called()


@freeze_time()
async def test_promocode_redemption_account_age_satisfied(
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **factories.AccountAgePromocodeInputFactory.build_python(),
        )

    assert promocode.max_account_age_days is not None
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{authorized_user_id}/"
    ).respond(
        json=DetailedUserFactory.build_json(
            created_at=datetime_utc_now()
            - timedelta(days=promocode.max_account_age_days)
        )
    )

    assert_nodata_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": promocode.code},
        ),
    )

    async with active_session():
        updated_promocode = await Promocode.find_first_by_id(promocode.id)
        assert updated_promocode is not None
        await updated_promocode.delete()

        updated_subscription = await Subscription.find_first_by_id(authorized_user_id)
        assert updated_subscription is not None
        await updated_subscription.delete()

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
    ("promocode_factory", "error"),
    [
        pytest.param(
            factories.NotActiveYetPromocodeInputFactory,
            "Promocode not active yet",
            id="not_active_yet",
        ),
        pytest.param(
            factories.ExpiredPromocodeInputFactory,
            "Promocode expired",
            id="expired",
        ),
    ],
)
async def test_promocode_redemption_outside_validity_period(
    active_session: ActiveSession,
    authorized_client: TestClient,
    promocode_factory: type[BaseModelFactory[Promocode.InputSchema]],
    error: str,
) -> None:
    async with active_session():
        promocode = await Promocode.create(**promocode_factory.build_python())

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


async def test_promocode_redemption_already_redeemed(
    active_session: ActiveSession,
    authorized_user_id: int,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **factories.UnrestrictedPromocodeInputFactory.build_python(),
        )
        await PromocodeRedemption.create(
            promocode_id=promocode.id, user_id=authorized_user_id
        )

    assert_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": promocode.code},
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode already redeemed"},
    )

    async with active_session():
        await promocode.delete()


async def test_promocode_redemption_usage_limit_reached(
    active_session: ActiveSession,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.UnrestrictedPromocodeInputFactory.build_python(),
                **factories.AtLimitPromocodeUsageStateFactory.build_python(),
            },
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


async def test_promocode_redemption_max_account_age_exceeded(
    active_session: ActiveSession,
    users_internal_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **factories.AccountAgePromocodeInputFactory.build_python(),
        )

    assert promocode.max_account_age_days is not None
    users_internal_respx_mock.get(path=f"/users/{authorized_user_id}/").respond(
        json=DetailedUserFactory.build_json(
            created_at=datetime_utc_now()
            - timedelta(days=promocode.max_account_age_days + 1)
        )
    )

    assert_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": promocode.code},
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode max account age exceeded"},
    )

    async with active_session():
        await promocode.delete()


async def test_promocode_redemption_already_redeemed_concurrently(
    active_session: ActiveSession,
    mock_stack: MockStack,
    authorized_user_id: int,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **factories.UnrestrictedPromocodeInputFactory.build_python(),
        )
        await PromocodeRedemption.create(
            promocode_id=promocode.id, user_id=authorized_user_id
        )

    mock_stack.enter_async_mock(
        PromocodeRedemption, "is_present_by_ids", return_value=False
    )

    assert_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/promocode-redemptions/",
            json={"code": promocode.code},
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Promocode already redeemed"},
    )

    async with active_session():
        updated_promocode = await Promocode.find_first_by_id(promocode.id)
        assert updated_promocode is not None
        assert_contains(updated_promocode, {"usage_count": promocode.usage_count})

        assert await Subscription.find_first_by_id(authorized_user_id) is None

        await updated_promocode.delete()


async def test_promocode_redemption_usage_limit_reached_concurrently(
    active_session: ActiveSession,
    mock_stack: MockStack,
    authorized_user_id: int,
    authorized_client: TestClient,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **factories.UnrestrictedPromocodeInputFactory.build_python(),
        )

    mock_stack.enter_async_mock(
        Promocode, "find_and_increment_usage_count_by_id", return_value=None
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
        redemption = await PromocodeRedemption.find_first_by_kwargs(
            promocode_id=promocode.id, user_id=authorized_user_id
        )
        assert redemption is not None

        assert await Subscription.find_first_by_id(authorized_user_id) is None

        await promocode.delete()

        assert await Subscription.find_first_by_id(authorized_user_id) is None
