from typing import Any

import pytest
from freezegun import freeze_time
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    Classroom,
    ClassroomKind,
    ClassroomStatus,
    GroupClassroom,
)
from app.common.utils.datetime import datetime_utc_now
from tests.classrooms.factories import (
    ClassroomStatusUpdateFactory,
    GroupClassroomInputFactory,
    GroupClassroomPatchFactory,
    IndividualClassroomPatchFactory,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_group_classroom_creation(
    mock_stack: MockStack,
    active_session: ActiveSession,
    tutor_client: TestClient,
) -> None:
    validate_subject_mock = mock_stack.enter_async_mock(
        "app.classrooms.routes.classrooms_tutor_rst.validate_subject",
    )

    input_data: AnyJSON = GroupClassroomInputFactory.build_json()

    classroom_id = assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor/group-classrooms/",
            json=input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            "id": int,
            "kind": ClassroomKind.GROUP,
            "status": ClassroomStatus.ACTIVE,
            "created_at": datetime_utc_now(),
            **input_data,
        },
    ).json()["id"]

    async with active_session():
        classroom = await GroupClassroom.find_first_by_id(classroom_id)
        assert classroom is not None
        await classroom.delete()

    validate_subject_mock.assert_awaited_once_with(
        new_subject_id=input_data["subject_id"]
    )


async def test_classroom_retrieving(
    tutor_client: TestClient,
    any_classroom: AnyClassroom,
    any_classroom_tutor_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            f"/api/protected/classroom-service/roles/tutor/classrooms/{any_classroom.id}/",
        ),
        expected_json=any_classroom_tutor_data,
    )


async def test_individual_classroom_updating(
    mock_stack: MockStack,
    tutor_client: TestClient,
    individual_classroom: GroupClassroom,
    individual_classroom_tutor_data: AnyJSON,
) -> None:
    validate_subject_mock = mock_stack.enter_async_mock(
        "app.classrooms.routes.classrooms_tutor_rst.validate_subject",
    )

    patch_data: AnyJSON = IndividualClassroomPatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            f"/api/protected/classroom-service/roles/tutor/individual-classrooms/{individual_classroom.id}/",
            json=patch_data,
        ),
        expected_json={
            **individual_classroom_tutor_data,
            **patch_data,
        },
    )

    validate_subject_mock.assert_awaited_once_with(
        new_subject_id=patch_data.get("subject_id"),
        old_subject_id=individual_classroom.subject_id,
    )


async def test_group_classroom_updating(
    mock_stack: MockStack,
    tutor_client: TestClient,
    group_classroom: GroupClassroom,
    group_classroom_tutor_data: AnyJSON,
) -> None:
    validate_subject_mock = mock_stack.enter_async_mock(
        "app.classrooms.routes.classrooms_tutor_rst.validate_subject",
    )

    patch_data: AnyJSON = GroupClassroomPatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            f"/api/protected/classroom-service/roles/tutor/group-classrooms/{group_classroom.id}/",
            json=patch_data,
        ),
        expected_json={
            **group_classroom_tutor_data,
            **patch_data,
        },
    )

    validate_subject_mock.assert_awaited_once_with(
        new_subject_id=patch_data.get("subject_id"),
        old_subject_id=group_classroom.subject_id,
    )


@pytest.mark.parametrize(
    "new_status",
    [
        pytest.param(status, id=status.value)
        for status in ClassroomStatus
        if status is not ClassroomStatus.LOCKED
    ],
)
async def test_classroom_status_updating(
    active_session: ActiveSession,
    tutor_client: TestClient,
    any_classroom: AnyClassroom,
    any_classroom_tutor_data: AnyJSON,
    new_status: ClassroomStatus,
) -> None:
    assert_nodata_response(
        tutor_client.put(
            f"/api/protected/classroom-service/roles/tutor/classrooms/{any_classroom.id}/status/",
            json={"status": new_status},
        )
    )

    async with active_session() as session:
        session.add(any_classroom)
        await session.refresh(any_classroom)

        assert any_classroom.status is new_status


async def test_classroom_deleting(
    active_session: ActiveSession,
    tutor_client: TestClient,
    any_classroom: AnyClassroom,
    any_classroom_tutor_data: AnyJSON,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            f"/api/protected/classroom-service/roles/tutor/classrooms/{any_classroom.id}/",
        )
    )

    async with active_session():
        assert await Classroom.find_first_by_id(any_classroom.id) is None


classroom_request_parametrization = pytest.mark.parametrize(
    ("method", "collection", "path", "body_factory", "classroom"),
    [
        pytest.param(
            "GET",
            "classrooms",
            "",
            None,
            lf("any_classroom"),
            id="retrieve_classroom",
        ),
        pytest.param(
            "PATCH",
            "individual-classrooms",
            "",
            IndividualClassroomPatchFactory,
            lf("individual_classroom"),
            id="update_individual_classroom",
        ),
        pytest.param(
            "PATCH",
            "group-classrooms",
            "",
            GroupClassroomPatchFactory,
            lf("group_classroom"),
            id="update_group_classroom",
        ),
        pytest.param(
            "PUT",
            "classrooms",
            "status/",
            ClassroomStatusUpdateFactory,
            lf("any_classroom"),
            id="update_classroom_status",
        ),
        pytest.param(
            "DELETE",
            "classrooms",
            "",
            None,
            lf("any_classroom"),
            id="delete_classroom",
        ),
    ],
)


@classroom_request_parametrization
async def test_classroom_requesting_access_denied(
    outsider_client: TestClient,
    method: str,
    collection: str,
    path: str,
    body_factory: type[BaseModelFactory[Any]] | None,
    classroom: AnyClassroom,
) -> None:
    assert_response(
        outsider_client.request(
            method,
            f"/api/protected/classroom-service/roles/tutor/{collection}/{classroom.id}/{path}",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Classroom tutor access denied"},
    )


@classroom_request_parametrization
async def test_classroom_not_finding(
    active_session: ActiveSession,
    tutor_client: TestClient,
    method: str,
    collection: str,
    path: str,
    body_factory: type[BaseModelFactory[Any]] | None,
    classroom: AnyClassroom,
) -> None:
    async with active_session():
        await Classroom.delete_by_kwargs(id=classroom.id)

    assert_response(
        tutor_client.request(
            method,
            f"/api/protected/classroom-service/roles/tutor/{collection}/{classroom.id}/{path}",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom not found"},
    )
