import pytest
from starlette.testclient import TestClient

from app.common.schemas.subscriptions_sch import PlanSchema
from app.subscriptions.models.subscriptions_db import Subscription
from tests.common.assert_contains_ext import assert_response
from tests.subscriptions.conftest import plan_parametrization

pytestmark = pytest.mark.anyio


@plan_parametrization
async def test_user_plan_retrieving(
    internal_client: TestClient,
    authorized_user_id: int,
    subscription: Subscription | None,
    expected_plan_data: PlanSchema,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/subscription-service/users/{authorized_user_id}/plan/",
        ),
        expected_json=expected_plan_data.model_dump(mode="json"),
    )
