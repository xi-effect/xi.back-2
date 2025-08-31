from collections.abc import AsyncIterator, Sequence
from typing import Final

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.autocomplete.models.subjects_db import Subject
from tests.autocomplete.factories import SubjectInputFactory
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


SUBJECT_LIST_SIZE: Final[int] = 6


@pytest.fixture()
async def subjects(
    active_session: ActiveSession,
    faker: Faker,
    tutor_user_id: int,
) -> AsyncIterator[Sequence[Subject]]:
    subjects: list[Subject] = []
    async with active_session():
        for i in range(SUBJECT_LIST_SIZE):
            subjects.append(
                await Subject.create(
                    **SubjectInputFactory.build_python(),
                    tutor_id=None if i % 2 == 0 else tutor_user_id,
                )
            )

    yield subjects

    async with active_session():
        for subject in subjects:
            await subject.delete()


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
    subjects: Sequence[Subject],
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
    subjects: Sequence[Subject],
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
