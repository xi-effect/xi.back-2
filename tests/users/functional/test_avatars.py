from collections.abc import AsyncIterator
from io import BytesIO

import pytest
from faker import Faker
from PIL import Image
from pytest_lazy_fixtures import lfc
from starlette import status
from starlette.testclient import TestClient

from app.users.models.users_db import User
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import PytestRequest

pytestmark = pytest.mark.anyio


@pytest.fixture(
    params=[
        pytest.param(lfc(lambda faker: faker.graphic_webp_file(raw=True)), id="webp"),
        pytest.param(lfc(lambda faker: faker.graphic_png_file(raw=True)), id="png"),
    ]
)
def image_content(request: PytestRequest[bytes]) -> bytes:
    return request.param


@pytest.fixture()
def processed_image_content(image_content: bytes) -> bytes:
    image = Image.open(BytesIO(image_content))
    image.resize(User.avatar_shape)

    processed_image_buffer = BytesIO()
    image.save(processed_image_buffer, format="webp")

    processed_image_buffer.seek(0)
    return processed_image_buffer.read()


@pytest.fixture()
async def create_avatar(faker: Faker, user: User) -> AsyncIterator[None]:
    with user.avatar_path.open("wb") as f:
        f.write(faker.graphic_webp_file(raw=True))
    yield
    user.avatar_path.unlink(missing_ok=True)


async def test_avatar_uploading(
    authorized_client: TestClient,
    user: User,
    image_content: bytes,
    processed_image_content: bytes,
) -> None:
    assert_nodata_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/avatar/",
            files={"avatar": ("avatar.webp", image_content, "image/webp")},
        )
    )

    assert user.avatar_path.is_file()
    with user.avatar_path.open("rb") as f:
        assert f.read() == processed_image_content

    user.avatar_path.unlink()


async def test_avatar_uploading_wrong_format(
    faker: Faker,
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/avatar/",
            files={"avatar": ("avatar", faker.random.randbytes(100), "image/webp")},
        ),
        expected_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        expected_json={"detail": "Invalid image format"},
    )


@pytest.mark.usefixtures("create_avatar")
async def test_avatar_replacing(
    authorized_client: TestClient,
    user: User,
    image_content: bytes,
    processed_image_content: bytes,
) -> None:
    assert_nodata_response(
        authorized_client.put(
            "/api/protected/user-service/users/current/avatar/",
            files={"avatar": ("avatar.webp", image_content, "image/webp")},
        )
    )

    assert user.avatar_path.is_file()
    with user.avatar_path.open("rb") as f:
        assert f.read() == processed_image_content


@pytest.mark.usefixtures("create_avatar")
async def test_avatar_deletion(
    authorized_client: TestClient,
    user: User,
) -> None:
    assert_nodata_response(
        authorized_client.delete("/api/protected/user-service/users/current/avatar/")
    )

    assert not user.avatar_path.is_file()


@pytest.mark.usefixtures("create_avatar")
async def test_mub_user_deletion_with_avatar(
    mub_client: TestClient,
    user: User,
) -> None:
    assert_nodata_response(mub_client.delete(f"/mub/user-service/users/{user.id}/"))

    assert not user.avatar_path.is_file()
