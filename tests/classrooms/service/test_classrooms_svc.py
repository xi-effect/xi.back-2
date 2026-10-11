import pytest
from respx import MockRouter

from app.classrooms.models.classrooms_db import (
    Classroom,
    ClassroomStatus,
    GroupClassroom,
    IndividualClassroom,
)
from app.classrooms.services import classrooms_svc
from app.common.config import settings
from tests.classrooms import factories
from tests.common.active_session import ActiveSession
from tests.common.respx_ext import assert_last_httpx_request
from tests.factories import PlanFactory

pytestmark = pytest.mark.anyio


async def test_has_tutor_reached_active_classrooms_limit_under_the_limit(
    active_session: ActiveSession,
    subscriptions_respx_mock: MockRouter,
    tutor_user_id: int,
) -> None:
    subscriptions_bridge_mock = subscriptions_respx_mock.get(
        path=f"/users/{tutor_user_id}/plan/"
    ).respond(json=PlanFactory.build_json(max_active_classrooms=1))

    async with active_session():
        await GroupClassroom.create(
            **factories.GroupClassroomInputFactory.build_python(),
            enrollments_count=0,
            tutor_id=tutor_user_id,
            status=ClassroomStatus.PAUSED,
        )

    async with active_session():
        assert not await classrooms_svc.has_tutor_reached_active_classrooms_limit(
            tutor_id=tutor_user_id
        )

    assert_last_httpx_request(
        subscriptions_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )

    async with active_session():
        await Classroom.delete_by_kwargs(tutor_id=tutor_user_id)


async def test_has_tutor_reached_active_classrooms_limit_over_the_limit(
    active_session: ActiveSession,
    subscriptions_respx_mock: MockRouter,
    tutor_user_id: int,
    individual_classroom: IndividualClassroom,
    group_classroom: GroupClassroom,
) -> None:
    subscriptions_bridge_mock = subscriptions_respx_mock.get(
        path=f"/users/{tutor_user_id}/plan/"
    ).respond(json=PlanFactory.build_json(max_active_classrooms=2))

    async with active_session():
        assert await classrooms_svc.has_tutor_reached_active_classrooms_limit(
            tutor_id=tutor_user_id
        )

    assert_last_httpx_request(
        subscriptions_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )
