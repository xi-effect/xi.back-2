from collections.abc import Sequence

import pytest
from freezegun import freeze_time
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.tutorships_db import Tutorship
from app.common.utils.datetime import datetime_utc_now
from tests.classrooms.conftest import TUTORSHIPS_LIST_SIZE
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, TUTORSHIPS_LIST_SIZE, id="start_to_end"),
        pytest.param(0, TUTORSHIPS_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            TUTORSHIPS_LIST_SIZE // 2, TUTORSHIPS_LIST_SIZE, id="middle_to_end"
        ),
    ],
)
async def test_tutor_tutorships_listing(
    mub_client: TestClient,
    tutor_user_id: int,
    tutor_tutorships: Sequence[Tutorship],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/classroom-service/tutors/{tutor_user_id}/students/",
            params=remove_none_values(
                {
                    "created_before": (
                        None
                        if offset == 0
                        else tutor_tutorships[offset - 1].created_at.isoformat()
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=[
            Tutorship.TutorResponseSchema.model_validate(
                tutorship, from_attributes=True
            )
            for tutorship in tutor_tutorships
        ][offset:limit],
    )


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, TUTORSHIPS_LIST_SIZE, id="start_to_end"),
        pytest.param(0, TUTORSHIPS_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            TUTORSHIPS_LIST_SIZE // 2, TUTORSHIPS_LIST_SIZE, id="middle_to_end"
        ),
    ],
)
async def test_student_tutorships_listing(
    mub_client: TestClient,
    student_user_id: int,
    student_tutorships: Sequence[Tutorship],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/classroom-service/students/{student_user_id}/tutors/",
            params=remove_none_values(
                {
                    "created_before": (
                        None
                        if offset == 0
                        else student_tutorships[offset - 1].created_at.isoformat()
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=[
            Tutorship.StudentResponseSchema.model_validate(
                tutorship, from_attributes=True
            )
            for tutorship in student_tutorships
        ][offset:limit],
    )


@freeze_time()
async def test_tutorship_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
    tutor_user_id: int,
    student_user_id: int,
) -> None:
    assert_response(
        mub_client.post(
            f"/mub/classroom-service/tutors/{tutor_user_id}/students/{student_user_id}/",
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            "created_at": datetime_utc_now(),
            "active_classroom_count": 0,
        },
    )

    async with active_session():
        tutorship = await Tutorship.find_first_by_kwargs(
            tutor_id=tutor_user_id,
            student_id=student_user_id,
        )
        assert tutorship is not None
        await tutorship.delete()


async def test_tutorship_creation_target_is_the_source(
    mub_client: TestClient,
    tutor_user_id: int,
) -> None:
    assert_response(
        mub_client.post(
            f"/mub/classroom-service/tutors/{tutor_user_id}/students/{tutor_user_id}/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Target is the source"},
    )


async def test_tutorship_creation_tutorship_already_exists(
    mub_client: TestClient,
    tutorship: Tutorship,
) -> None:
    assert_response(
        mub_client.post(
            f"/mub/classroom-service/tutors/{tutorship.tutor_id}/students/{tutorship.student_id}/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Tutorship already exists"},
    )


async def test_tutorship_retrieving(
    mub_client: TestClient,
    tutorship: Tutorship,
    tutorship_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/classroom-service/tutors/{tutorship.tutor_id}/students/{tutorship.student_id}/",
        ),
        expected_json=tutorship_data,
    )


async def test_tutorship_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    tutorship: Tutorship,
) -> None:
    assert_nodata_response(
        mub_client.delete(
            f"/mub/classroom-service/tutors/{tutorship.tutor_id}/students/{tutorship.student_id}/",
        )
    )

    async with active_session():
        assert (
            await Tutorship.find_first_by_kwargs(
                tutor_id=tutorship.tutor_id,
                student_id=tutorship.student_id,
            )
            is None
        )


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("GET", id="retrieve"),
        pytest.param("DELETE", id="delete"),
    ],
)
async def test_tutorship_not_finding(
    mub_client: TestClient,
    tutor_user_id: int,
    student_user_id: int,
    method: str,
) -> None:
    assert_response(
        mub_client.request(
            method=method,
            url=f"/mub/classroom-service/tutors/{tutor_user_id}/students/{student_user_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Tutorship not found"},
    )
