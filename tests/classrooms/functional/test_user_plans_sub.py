from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains
from respx import MockRouter

from app.classrooms.models.classrooms_db import (
    Classroom,
    ClassroomStatus,
    GroupClassroom,
    IndividualClassroom,
)
from app.classrooms.routes.user_plans_sub import sync_classroom_locks_with_user_plan
from app.common.config import settings
from app.common.config_bdg import subscriptions_bridge
from app.common.schemas.subscriptions_sch import PaidPlanKind, UserPlanUpdateEventSchema
from tests.classrooms import factories
from tests.common.active_session import ActiveSession
from tests.common.respx_ext import assert_last_httpx_request
from tests.factories import PlanFactory

pytestmark = pytest.mark.anyio


async def test_classroom_locks_syncing_with_free_plan(
    faker: Faker,
    active_session: ActiveSession,
    subscriptions_respx_mock: MockRouter,
    tutor_user_id: int,
) -> None:
    initial_active_classrooms_count: int = faker.random_int(min=2, max=5)

    async with active_session():
        for index in range(initial_active_classrooms_count):
            if index % 2 == 0:
                await IndividualClassroom.create(
                    **factories.IndividualClassroomInputFactory.build_python(),
                    tutor_id=tutor_user_id,
                    student_id=tutor_user_id + index + 1,
                    tutor_name=faker.name(),
                    student_name=faker.name(),
                    status=ClassroomStatus.ACTIVE,
                )
            else:
                await GroupClassroom.create(
                    **factories.GroupClassroomInputFactory.build_python(),
                    tutor_id=tutor_user_id,
                    enrollments_count=0,
                    status=ClassroomStatus.ACTIVE,
                )

    subscriptions_bridge_mock = subscriptions_respx_mock.get(
        path=f"/users/{tutor_user_id}/plan/"
    ).respond(json=PlanFactory.build_json(kind=None))

    event_data = UserPlanUpdateEventSchema(user_id=tutor_user_id)
    sync_classroom_locks_with_user_plan.mock.reset_mock()
    await subscriptions_bridge.publish_user_plan_update(data=event_data)
    sync_classroom_locks_with_user_plan.mock.assert_called_once_with(
        event_data.model_dump(mode="json")
    )

    async with active_session():
        assert_contains(
            [
                classroom.status
                for classroom in await Classroom.find_all_by_kwargs(
                    Classroom.created_at.desc(), tutor_id=tutor_user_id
                )
            ],
            [ClassroomStatus.LOCKED for _ in range(initial_active_classrooms_count)],
        )
        await Classroom.delete_by_kwargs(tutor_id=tutor_user_id)

    assert_last_httpx_request(
        subscriptions_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_classroom_locks_syncing_with_paid_plan(
    faker: Faker,
    active_session: ActiveSession,
    subscriptions_respx_mock: MockRouter,
    tutor_user_id: int,
) -> None:
    initial_active_classrooms_count: int = faker.random_int(min=1, max=5)
    max_active_classrooms_count: int = (
        initial_active_classrooms_count + faker.random_int(min=1, max=5)
    )
    remaining_locked_classrooms_count: int = faker.random_int(min=1, max=5)
    initial_locked_classrooms_count: int = (
        max_active_classrooms_count
        - initial_active_classrooms_count
        + remaining_locked_classrooms_count
    )

    created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    async with active_session():
        for index in range(
            initial_active_classrooms_count + initial_locked_classrooms_count
        ):
            status = (
                ClassroomStatus.ACTIVE
                if index < initial_active_classrooms_count
                else ClassroomStatus.LOCKED
            )
            if index % 2 == 0:
                await IndividualClassroom.create(
                    **factories.IndividualClassroomInputFactory.build_python(),
                    tutor_id=tutor_user_id,
                    student_id=tutor_user_id + index + 1,
                    tutor_name=faker.name(),
                    student_name=faker.name(),
                    status=status,
                    created_at=created_at,
                )
            else:
                await GroupClassroom.create(
                    **factories.GroupClassroomInputFactory.build_python(),
                    tutor_id=tutor_user_id,
                    enrollments_count=0,
                    status=status,
                    created_at=created_at,
                )
            created_at -= timedelta(minutes=faker.random_int(min=1))

    subscriptions_bridge_mock = subscriptions_respx_mock.get(
        path=f"/users/{tutor_user_id}/plan/"
    ).respond(
        json=PlanFactory.build_json(
            kind=PaidPlanKind.PRO, max_active_classrooms=max_active_classrooms_count
        )
    )

    event_data = UserPlanUpdateEventSchema(user_id=tutor_user_id)
    sync_classroom_locks_with_user_plan.mock.reset_mock()
    await subscriptions_bridge.publish_user_plan_update(data=event_data)
    sync_classroom_locks_with_user_plan.mock.assert_called_once_with(
        event_data.model_dump(mode="json")
    )

    async with active_session():
        assert_contains(
            [
                classroom.status
                for classroom in await Classroom.find_all_by_kwargs(
                    Classroom.created_at.desc(), tutor_id=tutor_user_id
                )
            ],
            [ClassroomStatus.ACTIVE for _ in range(max_active_classrooms_count)]
            + [
                ClassroomStatus.LOCKED for _ in range(remaining_locked_classrooms_count)
            ],
        )
        await Classroom.delete_by_kwargs(tutor_id=tutor_user_id)

    assert_last_httpx_request(
        subscriptions_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )
