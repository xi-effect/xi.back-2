import pytest
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import AnyTag, Tag
from app.common.schemas.autocomplete_sch import TagKind
from tests.autocomplete.conftest import TAG_LIST_SIZE
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, TAG_LIST_SIZE, id="start_to_end"),
        pytest.param(0, TAG_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            TAG_LIST_SIZE // 2,
            TAG_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_listing_tags_by_tutor(
    mub_client: TestClient,
    tutor_user_id: int,
    parametrized_tag_kind: TagKind,
    tags: list[AnyTag],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/",
            params={
                "offset": offset,
                "limit": limit,
                "tutor_id": tutor_user_id,
            },
        ),
        expected_json=[
            Tag.ResponseMUBSchema.model_validate(tag, from_attributes=True)
            for tag in tags
        ][offset:limit],
    )


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, TAG_LIST_SIZE // 2, id="start_to_end"),
        pytest.param(0, TAG_LIST_SIZE // 4, id="start_to_middle"),
        pytest.param(
            TAG_LIST_SIZE // 4,
            TAG_LIST_SIZE // 2,
            id="middle_to_end",
        ),
    ],
)
async def test_listing_common_tags(
    mub_client: TestClient,
    parametrized_tag_kind: TagKind,
    tags: list[AnyTag],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/",
            params={
                "offset": offset,
                "limit": limit,
            },
        ),
        expected_json=[
            Tag.ResponseMUBSchema.model_validate(tag, from_attributes=True)
            for tag in tags
            if tag.tutor_id is None
        ][offset:limit],
    )
