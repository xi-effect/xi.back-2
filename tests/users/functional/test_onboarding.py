import pytest
from starlette.testclient import TestClient

from app.users.models.users_db import OnboardingStage, User
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.users import factories
from tests.users.utils import get_db_user


@pytest.mark.anyio()
async def test_proceeding_to_community_choice_in_onboarding(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
) -> None:
    assert_nodata_response(
        authorized_client.put(
            "/api/protected/user-service/onboarding/stages/community-choice/",
            json=factories.CommunityChoiceFactory.build_json(),
        )
    )

    async with active_session():
        assert (
            await get_db_user(user)
        ).onboarding_stage is OnboardingStage.COMMUNITY_CHOICE


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("current_stage", "target_stage"),
    [
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMPLETED),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMPLETED),
    ],
)
async def test_proceeding_in_onboarding(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_nodata_response(
        authorized_client.put(
            f"/api/protected/user-service/onboarding/stages/{target_stage.value}/"
        )
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is target_stage


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("current_stage", "target_stage"),
    [
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.CREATED, OnboardingStage.COMPLETED),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMPLETED),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMPLETED),
    ],
)
async def test_proceeding_in_onboarding_invalid_transition(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_response(
        authorized_client.put(
            f"/api/protected/user-service/onboarding/stages/{target_stage.value}/",
        ),
        expected_json={"detail": "Invalid transition"},
        expected_code=409,
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is current_stage


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("current_stage", "target_stage"),
    [
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.CREATED),
    ],
)
async def test_returning_in_onboarding(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_nodata_response(
        authorized_client.delete(
            f"/api/protected/user-service/onboarding/stages/{current_stage.value}/"
        )
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is target_stage


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("current_stage", "target_stage"),
    [
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_INVITE),
    ],
)
async def test_returning_in_onboarding_invalid_transition(
    active_session: ActiveSession,
    authorized_client: TestClient,
    user: User,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_response(
        authorized_client.delete(
            f"/api/protected/user-service/onboarding/stages/{target_stage.value}/",
        ),
        expected_json={"detail": "Invalid transition"},
        expected_code=409,
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is current_stage
