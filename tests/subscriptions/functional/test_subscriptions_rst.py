import pytest
from starlette import status
from starlette.testclient import TestClient

from app.subscriptions.models.auto_renewals_db import AutoRenewal
from app.subscriptions.models.subscriptions_db import Subscription
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import repackage_json

pytestmark = pytest.mark.anyio


async def test_current_subscription_retrieving(
    authorized_client: TestClient,
    parametrized_subscription: Subscription,
    parametrized_auto_renewal: AutoRenewal | None,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/subscription-service/users/current/subscription/",
        ),
        expected_json={
            "subscription": repackage_json(
                Subscription.ResponseSchema,
                parametrized_subscription,
            ),
            "auto_renewal": (
                None
                if parametrized_auto_renewal is None
                else repackage_json(
                    AutoRenewal.ResponseSchema,
                    parametrized_auto_renewal,
                )
            ),
        },
    )


async def test_current_subscription_retrieving_subscription_not_found(
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/subscription-service/users/current/subscription/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Subscription not found"},
    )
