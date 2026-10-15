import pytest
from faker import Faker
from respx import MockRouter

from app.common.config import settings
from app.content.models.files_db import File, FileKind
from app.content.models.ydocs_db import YDoc, YDocContentKind
from app.content.services import storage_svc
from tests.common.active_session import ActiveSession
from tests.common.respx_ext import assert_last_httpx_request
from tests.factories import HighStorageLimitPlanFactory, PlanFactory

pytestmark = pytest.mark.anyio


async def test_has_owner_reached_storage_limit_under_the_limit(
    active_session: ActiveSession,
    subscriptions_respx_mock: MockRouter,
    tutor_user_id: int,
) -> None:
    subscriptions_bridge_mock = subscriptions_respx_mock.get(
        path=f"/users/{tutor_user_id}/plan/"
    ).respond(json=HighStorageLimitPlanFactory.build_json())

    async with active_session():
        assert not await storage_svc.has_owner_reached_storage_limit(
            owner_id=tutor_user_id
        )

    assert_last_httpx_request(
        subscriptions_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_has_owner_reached_storage_limit_over_the_limit(
    faker: Faker,
    active_session: ActiveSession,
    subscriptions_respx_mock: MockRouter,
    tutor_user_id: int,
) -> None:
    file_size: int = faker.pyint(min_value=1, max_value=10**6)
    ydoc_size: int = faker.pyint(min_value=1, max_value=10**6)

    subscriptions_bridge_mock = subscriptions_respx_mock.get(
        path=f"/users/{tutor_user_id}/plan/"
    ).respond(
        json=PlanFactory.build_json(
            max_total_storage_bytes=faker.pyint(
                min_value=1, max_value=file_size + ydoc_size
            )
        )
    )

    async with active_session():
        await File.create(
            owner_id=tutor_user_id,
            uploader_id=tutor_user_id,
            name=faker.word(),
            extension=faker.file_extension(),
            kind=FileKind.UNCATEGORIZED,
            content_type=faker.mime_type(),
            size_bytes=file_size,
            file_tags=[],
        )
        await YDoc.create(
            owner_id=tutor_user_id,
            content_kind=YDocContentKind.NOTE,
            size_bytes=ydoc_size,
        )

    async with active_session():
        assert await storage_svc.has_owner_reached_storage_limit(owner_id=tutor_user_id)

    assert_last_httpx_request(
        subscriptions_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )

    async with active_session():
        await File.delete_by_kwargs(owner_id=tutor_user_id)
        await YDoc.delete_by_kwargs(owner_id=tutor_user_id)
