import pytest
from faker import Faker
from respx import MockRouter

from app.classrooms.models.classrooms_db import GroupClassroom, IndividualClassroom
from app.classrooms.services import classrooms_svc
from app.common.config import settings
from tests.common.active_session import ActiveSession
from tests.common.respx_ext import assert_last_httpx_request
from tests.factories import PlanFactory

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "is_active_classrooms_limit_reached",
    [
        pytest.param(False, id="limit_not_reached"),
        pytest.param(True, id="limit_reached"),
    ],
)
async def test_has_tutor_reached_active_classrooms_limit(
    faker: Faker,
    active_session: ActiveSession,
    subscriptions_respx_mock: MockRouter,
    tutor_user_id: int,
    individual_classroom: IndividualClassroom,
    group_classroom: GroupClassroom,
    is_active_classrooms_limit_reached: bool,
) -> None:
    max_active_classrooms = (
        faker.pyint(min_value=0, max_value=2)
        if is_active_classrooms_limit_reached
        else faker.pyint(min_value=3, max_value=100)
    )

    subscriptions_bridge_mock = subscriptions_respx_mock.get(
        path=f"/users/{tutor_user_id}/plan/"
    ).respond(json=PlanFactory.build_json(max_active_classrooms=max_active_classrooms))

    async with active_session():
        assert (
            await classrooms_svc.has_tutor_reached_active_classrooms_limit(
                tutor_id=tutor_user_id
            )
            is is_active_classrooms_limit_reached
        )

    assert_last_httpx_request(
        subscriptions_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )
