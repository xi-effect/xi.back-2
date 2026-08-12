import pytest
from pydantic_marshals.contains import UnorderedLiteralCollection
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    GroupClassroom,
    IndividualClassroom,
)
from app.classrooms.models.enrollments_db import Enrollment
from app.common.schemas.classrooms_sch import ClassroomRole
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import remove_none_values

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("classroom", "role", "expected_participant_ids"),
    [
        pytest.param(
            lf("individual_classroom"),
            ClassroomRole.TUTOR,
            lfc(lambda individual_classroom: [individual_classroom.tutor_id]),
            id="individual_classroom-tutor",
        ),
        pytest.param(
            lf("individual_classroom"),
            ClassroomRole.STUDENT,
            lfc(lambda individual_classroom: [individual_classroom.student_id]),
            id="individual_classroom-student",
        ),
        pytest.param(
            lf("individual_classroom"),
            None,
            lfc(
                lambda individual_classroom: [
                    individual_classroom.tutor_id,
                    individual_classroom.student_id,
                ]
            ),
            id="individual_classroom-no_filter",
        ),
        pytest.param(
            lf("group_classroom"),
            ClassroomRole.TUTOR,
            lfc(lambda group_classroom: [group_classroom.tutor_id]),
            id="group_classroom-tutor",
        ),
        pytest.param(
            lf("group_classroom"),
            ClassroomRole.STUDENT,
            [],
            id="group_classroom-student-no_enrollment",
        ),
        pytest.param(
            lf("group_classroom"),
            ClassroomRole.STUDENT,
            lfc(lambda enrollment: [enrollment.student_id]),
            id="group_classroom-student-with_enrollment",
        ),
        pytest.param(
            lf("group_classroom"),
            None,
            lfc(lambda group_classroom: [group_classroom.tutor_id]),
            id="group_classroom-no_filter-no_enrollment",
        ),
        pytest.param(
            lf("group_classroom"),
            None,
            lfc(
                lambda group_classroom, enrollment: [
                    group_classroom.tutor_id,
                    enrollment.student_id,
                ]
            ),
            id="group_classroom-no_filter-with_enrollment",
        ),
    ],
)
async def test_listing_classroom_participant_ids(
    internal_client: TestClient,
    classroom: AnyClassroom,
    role: ClassroomRole | None,
    expected_participant_ids: list[int],
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/classroom-service/classrooms/{classroom.id}/participant-ids/",
            params=remove_none_values({"role": role}),
        ),
        expected_json=expected_participant_ids,
    )


async def test_listing_classroom_participant_ids_classroom_not_found(
    internal_client: TestClient,
    deleted_group_classroom_id: int,
) -> None:
    assert_response(
        internal_client.get(
            "/internal/classroom-service"
            f"/classrooms/{deleted_group_classroom_id}/participant-ids/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom not found"},
    )


async def test_listing_tutor_classroom_ids(
    internal_client: TestClient,
    tutor_user_id: int,
    individual_classroom: IndividualClassroom,
    group_classroom: GroupClassroom,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/classroom-service/tutors/{tutor_user_id}/classroom-ids/",
        ),
        expected_json=UnorderedLiteralCollection(
            [individual_classroom.id, group_classroom.id],
        ),
    )


async def test_listing_student_classroom_ids(
    internal_client: TestClient,
    student_user_id: int,
    individual_classroom: IndividualClassroom,
    enrollment: Enrollment,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/classroom-service/students/{student_user_id}/classroom-ids/",
        ),
        expected_json=UnorderedLiteralCollection(
            [individual_classroom.id, enrollment.group_classroom_id],
        ),
    )
