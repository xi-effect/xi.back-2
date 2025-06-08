import pytest
from faker import Faker
from starlette import status
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
        pytest.param("GET", "/channels/1/board/", id="retrieve-board-channel"),
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
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Invalid key"},
    )


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
        pytest.param(
            "GET",
            "/channels/1/board/access-level/",
            id="retrieve-board-channel-access-level",
        ),
    ],
)
async def test_requesting_internal_invalid_key(
    faker: Faker,
    client: TestClient,
    pass_token: bool,
    method: str,
    path: str,
) -> None:
    headers = {"X-Api-Key": faker.pystr()} if pass_token else None
    assert_response(
        client.request(method, f"/internal/community-service{path}", headers=headers),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Invalid key"},
    )
