import pytest
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import AnyTag
from app.common.schemas.autocomplete_sch import TagKind
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_retrieving_multiple_tags(
    internal_client: TestClient,
    parametrized_tag_kind: TagKind,
    tag: AnyTag,
    tag_data: AnyJSON,
    other_tag: AnyTag,
    other_tag_data: AnyJSON,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/",
            params={"tag_ids": [tag.id, other_tag.id]},
        ),
        expected_json={
            str(tag.id): tag_data,
            str(other_tag.id): other_tag_data,
        },
    )


async def test_retrieving_multiple_tags_tag_not_found(
    internal_client: TestClient,
    parametrized_tag_kind: TagKind,
    deleted_tag_id: int,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/",
            params={"tag_ids": [deleted_tag_id]},
        ),
        expected_json={},
    )
