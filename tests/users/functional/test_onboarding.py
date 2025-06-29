import pytest
from starlette import status
from starlette.testclient import TestClient

from app.users.models.users_db import OnboardingStage, User
from app.users.routes.onboarding_rst import VALID_TRANSITIONS_BY_MODE, TransitionMode
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.users.utils import get_db_user

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("transition_mode", "current_stage", "target_stage"),
    [
        pytest.param(
            transition_mode,
            current_stage,
            target_stage,
            id=f"{transition_mode.value}-{current_stage}_{target_stage}",
        )
        for transition_mode in TransitionMode
        for current_stage, target_stage in VALID_TRANSITIONS_BY_MODE[transition_mode]
    ],
)
async def test_proceeding_in_onboarding(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
    transition_mode: TransitionMode,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_nodata_response(
        authorized_client.put(
            f"/api/protected/user-service/users/current/onboarding-stages/{target_stage.value}/",
            params={"transition_mode": transition_mode},
        )
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is target_stage


@pytest.mark.parametrize(
    ("transition_mode", "current_stage", "target_stage"),
    [
        pytest.param(
            transition_mode,
            current_stage,
            target_stage,
            id=f"{transition_mode.value}-{current_stage}_{target_stage}",
        )
        for transition_mode in TransitionMode
        for current_stage in OnboardingStage
        for target_stage in OnboardingStage
        if (current_stage, target_stage)
        not in VALID_TRANSITIONS_BY_MODE[transition_mode]
    ],
)
async def test_proceeding_in_onboarding_invalid_transition(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
    transition_mode: TransitionMode,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_response(
        authorized_client.put(
            f"/api/protected/user-service/users/current/onboarding-stages/{target_stage.value}/",
            params={"transition_mode": transition_mode},
        ),
        expected_json={"detail": "Invalid transition"},
        expected_code=status.HTTP_409_CONFLICT,
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is current_stage
