import pytest
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import SubjectTag
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_retrieving_multiple_subject_tags(
    internal_client: TestClient,
    subject_tag: SubjectTag,
    subject_tag_data: AnyJSON,
    other_subject_tag: SubjectTag,
    other_subject_tag_data: AnyJSON,
) -> None:
    assert_response(
        internal_client.get(
            "/internal/autocomplete-service/tag-kinds/subject/tags/",
            params={"tag_ids": [subject_tag.id, other_subject_tag.id]},
        ),
        expected_json={
            str(subject_tag.id): subject_tag_data,
            str(other_subject_tag.id): other_subject_tag_data,
        },
    )


async def test_retrieving_multiple_subject_tags_tag_not_found(
    internal_client: TestClient,
    deleted_subject_tag_id: int,
) -> None:
    assert_response(
        internal_client.get(
            "/internal/autocomplete-service/tag-kinds/subject/tags/",
            params={"tag_ids": [deleted_subject_tag_id]},
        ),
        expected_json={},
    )
