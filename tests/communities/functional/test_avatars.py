from collections.abc import AsyncIterator

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.communities.models.communities_db import Community
from tests.common.assert_contains_ext import assert_nodata_response, assert_response

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def image(faker: Faker) -> bytes:
    return faker.graphic_webp_file(raw=True)  # type: ignore[no-any-return]


@pytest.fixture()
async def _create_avatar(community: Community, image: bytes) -> AsyncIterator[None]:
    with community.avatar_path.open("wb") as f:
        f.write(image)
    yield
    community.avatar_path.unlink(missing_ok=True)


async def test_avatar_uploading(
    authorized_client: TestClient, community: Community, image: bytes
) -> None:
    assert_nodata_response(
        authorized_client.put(
            f"/api/protected/community-service/communities/{community.id}/avatar/",
            files={"avatar": ("avatar.webp", image, "image/webp")},
        )
    )

    assert community.avatar_path.is_file()
    with community.avatar_path.open("rb") as f:
        assert f.read() == image

    community.avatar_path.unlink()


async def test_avatar_uploading_wrong_format(
    faker: Faker, authorized_client: TestClient, community: Community
) -> None:
    assert_response(
        authorized_client.put(
            f"/api/protected/community-service/communities/{community.id}/avatar/",
            files={"avatar": ("avatar", faker.random.randbytes(100), "image/webp")},
        ),
        expected_code=415,
        expected_json={"detail": "Invalid image format"},
    )


@pytest.mark.usefixtures("_create_avatar")
async def test_avatar_replacing(
    faker: Faker, authorized_client: TestClient, community: Community
) -> None:
    image_2 = faker.graphic_webp_file(raw=True)
    assert_nodata_response(
        authorized_client.put(
            f"/api/protected/community-service/communities/{community.id}/avatar/",
            files={"avatar": ("avatar.webp", image_2, "image/webp")},
        )
    )

    assert community.avatar_path.is_file()
    with community.avatar_path.open("rb") as f:
        assert f.read() == image_2


@pytest.mark.usefixtures("_create_avatar")
async def test_avatar_deletion(
    authorized_client: TestClient, community: Community
) -> None:
    assert_nodata_response(
        authorized_client.delete(
            f"/api/protected/community-service/communities/{community.id}/avatar/"
        )
    )

    assert not community.avatar_path.is_file()


@pytest.mark.usefixtures("_create_avatar")
async def test_mub_community_deletion_with_avatar(
    mub_client: TestClient,
    community: Community,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/communities/{community.id}/")
    )

    assert not community.avatar_path.is_file()
