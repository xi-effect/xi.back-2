import pytest
from pytest_lazy_fixtures import lf
from starlette.testclient import TestClient

from app.autocomplete.models.subjects_db import Subject
from tests.autocomplete.conftest import SUBJECT_LIST_SIZE
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("search", "swap_case", "limit"),
    [
        pytest.param(
            lf("common_subject_name_prefix"),
            False,
            SUBJECT_LIST_SIZE,
            id="any-original_case-all",
        ),
        pytest.param(
            lf("common_subject_name_prefix"),
            False,
            SUBJECT_LIST_SIZE // 2,
            id="any-original_case-half",
        ),
        pytest.param(
            lf("common_subject_name_prefix"),
            True,
            SUBJECT_LIST_SIZE,
            id="any-swapped_case-all",
        ),
        pytest.param(
            lf("common_subject_name_prefix"),
            True,
            SUBJECT_LIST_SIZE // 2,
            id="any-swapped_case-half",
        ),
        pytest.param(
            lf("even_subject_name_suffix"),
            False,
            SUBJECT_LIST_SIZE,
            id="even_only-all",
        ),
        pytest.param(
            lf("even_subject_name_suffix"),
            False,
            SUBJECT_LIST_SIZE // 4,
            id="even_only-half",
        ),
        pytest.param(
            lf("odd_subject_name_suffix"),
            False,
            SUBJECT_LIST_SIZE,
            id="odd_only-original_case-all",
        ),
        pytest.param(
            lf("odd_subject_name_suffix"),
            False,
            SUBJECT_LIST_SIZE // 4,
            id="odd_only-original_case-half",
        ),
        pytest.param(
            lf("odd_subject_name_suffix"),
            True,
            SUBJECT_LIST_SIZE,
            id="odd_only-swapped_case-all",
        ),
        pytest.param(
            lf("odd_subject_name_suffix"),
            True,
            SUBJECT_LIST_SIZE // 4,
            id="odd_only-swapped_case-half",
        ),
        pytest.param(
            lf("excluded_from_subject_names"),
            False,
            SUBJECT_LIST_SIZE,
            id="no_results",
        ),
    ],
)
async def test_subject_autocompleting(
    tutor_client: TestClient,
    subjects: list[Subject],
    search: str,
    swap_case: bool,
    limit: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/autocomplete-service/subjects/autocomplete-suggestions/",
            params={
                "search": search.swapcase() if swap_case else search,
                "limit": limit,
            },
        ),
        expected_json=[
            Subject.ResponseSchema.model_validate(
                subject, from_attributes=True
            ).model_dump(mode="json", by_alias=True)
            for subject in subjects
            if search.lower() in subject.name.lower()
        ][:limit],
    )


async def test_subject_retrieving(
    tutor_client: TestClient,
    subject: Subject,
    subject_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(f"/api/protected/autocomplete-service/subjects/{subject.id}/"),
        expected_json=subject_data,
    )
