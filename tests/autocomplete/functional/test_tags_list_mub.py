import pytest
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import SubjectTag, Tag
from tests.autocomplete.conftest import SUBJECT_TAG_LIST_SIZE
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, SUBJECT_TAG_LIST_SIZE, id="start_to_end"),
        pytest.param(0, SUBJECT_TAG_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            SUBJECT_TAG_LIST_SIZE // 2,
            SUBJECT_TAG_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_subject_tags_by_tutor_listing(
    mub_client: TestClient,
    tutor_user_id: int,
    subject_tags: list[SubjectTag],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            "/mub/autocomplete-service/tag-kinds/subject/tags/",
            params={
                "offset": offset,
                "limit": limit,
                "tutor_id": tutor_user_id,
            },
        ),
        expected_json=[
            Tag.ResponseMUBSchema.model_validate(subject_tag, from_attributes=True)
            for subject_tag in subject_tags
        ][offset:limit],
    )


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, SUBJECT_TAG_LIST_SIZE // 2, id="start_to_end"),
        pytest.param(0, SUBJECT_TAG_LIST_SIZE // 4, id="start_to_middle"),
        pytest.param(
            SUBJECT_TAG_LIST_SIZE // 4,
            SUBJECT_TAG_LIST_SIZE // 2,
            id="middle_to_end",
        ),
    ],
)
async def test_common_subject_tags_listing(
    mub_client: TestClient,
    subject_tags: list[SubjectTag],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            "/mub/autocomplete-service/tag-kinds/subject/tags/",
            params={
                "offset": offset,
                "limit": limit,
            },
        ),
        expected_json=[
            Tag.ResponseMUBSchema.model_validate(subject_tag, from_attributes=True)
            for subject_tag in subject_tags
            if subject_tag.tutor_id is None
        ][offset:limit],
    )
