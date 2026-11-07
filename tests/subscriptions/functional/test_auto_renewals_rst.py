import pytest
from starlette import status
from starlette.testclient import TestClient

from app.subscriptions.models.auto_renewals_db import AutoRenewal
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response

pytestmark = pytest.mark.anyio


async def test_auto_renewal_cancelling(
    active_session: ActiveSession,
    authorized_client: TestClient,
    auto_renewal: AutoRenewal,
) -> None:
    assert_nodata_response(
        authorized_client.delete(
            "/api/protected/subscription-service/users/current/auto-renewal/",
        ),
    )

    async with active_session():
        assert await AutoRenewal.find_first_by_id(auto_renewal.user_id) is None


async def test_auto_renewal_cancelling_auto_renewal_not_found(
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.delete(
            "/api/protected/subscription-service/users/current/auto-renewal/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Auto-renewal not found"},
    )
