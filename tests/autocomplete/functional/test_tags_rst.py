import pytest
from pytest_lazy_fixtures import lf
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import SubjectTag, Tag
from tests.autocomplete.conftest import SUBJECT_TAG_LIST_SIZE
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("search", "swap_case", "limit"),
    [
        pytest.param(
            lf("common_subject_tag_name_prefix"),
            False,
            SUBJECT_TAG_LIST_SIZE,
            id="any-original_case-all",
        ),
        pytest.param(
            lf("common_subject_tag_name_prefix"),
            False,
            SUBJECT_TAG_LIST_SIZE // 2,
            id="any-original_case-half",
        ),
        pytest.param(
            lf("common_subject_tag_name_prefix"),
            True,
            SUBJECT_TAG_LIST_SIZE,
            id="any-swapped_case-all",
        ),
        pytest.param(
            lf("common_subject_tag_name_prefix"),
            True,
            SUBJECT_TAG_LIST_SIZE // 2,
            id="any-swapped_case-half",
        ),
        pytest.param(
            lf("even_subject_tag_name_suffix"),
            False,
            SUBJECT_TAG_LIST_SIZE,
            id="even_only-all",
        ),
        pytest.param(
            lf("even_subject_tag_name_suffix"),
            False,
            SUBJECT_TAG_LIST_SIZE // 4,
            id="even_only-half",
        ),
        pytest.param(
            lf("odd_subject_tag_name_suffix"),
            False,
            SUBJECT_TAG_LIST_SIZE,
            id="odd_only-original_case-all",
        ),
        pytest.param(
            lf("odd_subject_tag_name_suffix"),
            False,
            SUBJECT_TAG_LIST_SIZE // 4,
            id="odd_only-original_case-half",
        ),
        pytest.param(
            lf("odd_subject_tag_name_suffix"),
            True,
            SUBJECT_TAG_LIST_SIZE,
            id="odd_only-swapped_case-all",
        ),
        pytest.param(
            lf("odd_subject_tag_name_suffix"),
            True,
            SUBJECT_TAG_LIST_SIZE // 4,
            id="odd_only-swapped_case-half",
        ),
        pytest.param(
            lf("excluded_from_subject_tag_names"),
            False,
            SUBJECT_TAG_LIST_SIZE,
            id="no_results",
        ),
    ],
)
async def test_subject_tag_autocompleting(
    tutor_client: TestClient,
    subject_tags: list[SubjectTag],
    search: str,
    swap_case: bool,
    limit: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/autocomplete-service/tag-kinds/subject/autocomplete-suggestions/",
            params={
                "search": search.swapcase() if swap_case else search,
                "limit": limit,
            },
        ),
        expected_json=[
            Tag.ResponseSchema.model_validate(
                subject_tag, from_attributes=True
            ).model_dump(mode="json", by_alias=True)
            for subject_tag in subject_tags
            if search.lower() in subject_tag.name.lower()
        ][:limit],
    )


async def test_subject_tag_retrieving(
    tutor_client: TestClient,
    subject_tag: SubjectTag,
    subject_tag_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            f"/api/protected/autocomplete-service/tag-kinds/subject/tags/{subject_tag.id}/"
        ),
        expected_json=subject_tag_data,
    )
