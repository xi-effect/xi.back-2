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
        pytest.param("POST", "/post-channels/1/", id="create-post-channel"),
        pytest.param("DELETE", "/post-channels/1/", id="delete-post-channel"),
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
        client.request(method, f"/internal/post-service{path}", headers=headers),
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
        pytest.param("POST", "/post-channels/1/posts/", id="create-post"),
        pytest.param("GET", "/post-channels/1/posts/", id="list-posts"),
        pytest.param("GET", "/posts/1/", id="retrieve-post"),
        pytest.param("PATCH", "/posts/1/", id="update-post"),
        pytest.param("DELETE", "/posts/1/", id="delete-post"),
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
        client.request(method, f"/mub/post-service{path}", headers=headers),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Invalid key"},
    )
