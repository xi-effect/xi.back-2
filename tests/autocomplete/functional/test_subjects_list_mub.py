import pytest
from starlette.testclient import TestClient

from app.autocomplete.models.subjects_db import Subject
from tests.autocomplete.conftest import SUBJECT_LIST_SIZE
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, SUBJECT_LIST_SIZE, id="start_to_end"),
        pytest.param(0, SUBJECT_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            SUBJECT_LIST_SIZE // 2,
            SUBJECT_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_subjects_by_tutor_listing(
    mub_client: TestClient,
    tutor_user_id: int,
    subjects: list[Subject],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            "/mub/autocomplete-service/subjects/",
            params={
                "offset": offset,
                "limit": limit,
                "tutor_id": tutor_user_id,
            },
        ),
        expected_json=[
            Subject.ResponseMUBSchema.model_validate(subject, from_attributes=True)
            for subject in subjects
        ][offset:limit],
    )


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, SUBJECT_LIST_SIZE // 2, id="start_to_end"),
        pytest.param(0, SUBJECT_LIST_SIZE // 4, id="start_to_middle"),
        pytest.param(
            SUBJECT_LIST_SIZE // 4,
            SUBJECT_LIST_SIZE // 2,
            id="middle_to_end",
        ),
    ],
)
async def test_common_subjects_listing(
    mub_client: TestClient,
    subjects: list[Subject],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            "/mub/autocomplete-service/subjects/",
            params={
                "offset": offset,
                "limit": limit,
            },
        ),
        expected_json=[
            Subject.ResponseMUBSchema.model_validate(subject, from_attributes=True)
            for subject in subjects
            if subject.tutor_id is None
        ][offset:limit],
    )
