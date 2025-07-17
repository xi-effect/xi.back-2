import pytest
from faker import Faker
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from tests.common.assert_contains_ext import assert_response
from tests.common.mock_stack import MockStack

pytestmark = pytest.mark.anyio


async def test_feeding_updates_from_telegram_missing_configuration(
    mock_stack: MockStack,
    client: TestClient,
    supbot_webhook_url: str,
) -> None:
    mock_stack.enter_patch(settings, "supbot", new=None)

    assert_response(
        client.post(supbot_webhook_url),
        expected_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        expected_json={"detail": "Supbot configuration is missing"},
    )


@pytest.mark.parametrize(
    "pass_token",
    [
        pytest.param(False, id="missing_token"),
        pytest.param(True, id="invalid_token"),
    ],
)
async def test_feeding_updates_from_telegram_invalid_token(
    faker: Faker,
    client: TestClient,
    supbot_webhook_url: str,
    pass_token: bool,
) -> None:
    assert_response(
        client.post(
            supbot_webhook_url,
            headers={"X-Api-Key": faker.pystr()} if pass_token else None,
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Invalid webhook token"},
    )
