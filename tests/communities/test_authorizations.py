import pytest
from faker import Faker
from starlette.testclient import TestClient

from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "pass_token",
    [
        pytest.param(False, id="missing_token"),
        pytest.param(True, id="invalid_token"),
    ],
)
@pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param("POST", "/communities/", id="create-community"),
        pytest.param("GET", "/communities/1/", id="retrieve-community"),
        pytest.param("PATCH", "/communities/1/", id="update-community"),
        pytest.param("DELETE", "/communities/1/", id="delete-community"),
    ],
)
async def test_requesting_mub_invalid_key(
    faker: Faker,
    client: TestClient,
    pass_token: bool,
    method: str,
    path: str,
) -> None:
    headers = {"X-MUB-Secret": faker.pystr()} if pass_token else None
    assert_response(
        client.request(method, f"/mub/community-service{path}", headers=headers),
        expected_code=401,
        expected_json={"detail": "Invalid key"},
    )
