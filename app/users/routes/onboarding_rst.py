from enum import StrEnum, auto
from typing import Annotated

from fastapi import Query
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.users_dep import AuthorizedUser
from app.users.models.users_db import OnboardingStage

router = APIRouterExt(tags=["onboarding"])


class TransitionMode(StrEnum):
    FORWARDS = auto()
    BACKWARDS = auto()


VALID_TRANSITIONS_BY_MODE: dict[
    TransitionMode, set[tuple[OnboardingStage, OnboardingStage]]
] = {
    TransitionMode.FORWARDS: {
        (OnboardingStage.USER_INFORMATION, OnboardingStage.DEFAULT_LAYOUT),
        (OnboardingStage.DEFAULT_LAYOUT, OnboardingStage.NOTIFICATIONS),
        (OnboardingStage.NOTIFICATIONS, OnboardingStage.TRAINING),
        (OnboardingStage.TRAINING, OnboardingStage.COMPLETED),
    },
    TransitionMode.BACKWARDS: {
        (OnboardingStage.NOTIFICATIONS, OnboardingStage.DEFAULT_LAYOUT),
        (OnboardingStage.DEFAULT_LAYOUT, OnboardingStage.USER_INFORMATION),
    },
}


class OnboardingResponses(Responses):
    INVALID_TRANSITION = status.HTTP_409_CONFLICT, "Invalid transition"


@router.put(
    "/users/current/onboarding-stages/{stage}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=OnboardingResponses.responses(),
    summary="Update current user's onboarding stage",
)
async def update_onboarding_stage(
    user: AuthorizedUser,
    stage: OnboardingStage,
    transition_mode: Annotated[TransitionMode, Query()],
) -> None:
    if (user.onboarding_stage, stage) not in VALID_TRANSITIONS_BY_MODE[transition_mode]:
        raise OnboardingResponses.INVALID_TRANSITION
    user.onboarding_stage = stage
