from typing import Literal

from pydantic import BaseModel
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.users_dep import AuthorizedUser
from app.users.models.users_db import OnboardingStage, User

router = APIRouterExt(tags=["onboarding"])


class CommunityChoiceSchema(BaseModel):
    display_name: User.DisplayNameRequiredType


class OnboardingResponses(Responses):
    INVALID_TRANSITION = status.HTTP_409_CONFLICT, "Invalid transition"


ValidForwardStages = Literal[
    OnboardingStage.COMMUNITY_CHOICE,
    OnboardingStage.COMMUNITY_CREATE,
    OnboardingStage.COMMUNITY_INVITE,
    OnboardingStage.COMPLETED,
]

ValidReturnStages = Literal[
    OnboardingStage.COMMUNITY_CHOICE,
    OnboardingStage.COMMUNITY_CREATE,
    OnboardingStage.COMMUNITY_INVITE,
]

forward_valid_transitions: set[tuple[OnboardingStage, ValidForwardStages]] = {
    (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_CHOICE),
    (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_CREATE),
    (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_INVITE),
    (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMPLETED),
    (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMPLETED),
}

return_transitions: dict[ValidReturnStages, OnboardingStage] = {
    OnboardingStage.COMMUNITY_CHOICE: OnboardingStage.CREATED,
    OnboardingStage.COMMUNITY_CREATE: OnboardingStage.COMMUNITY_CHOICE,
    OnboardingStage.COMMUNITY_INVITE: OnboardingStage.COMMUNITY_CHOICE,
}


async def make_onboarding_transition(
    user: AuthorizedUser,
    stage: OnboardingStage,
) -> None:
    if (user.onboarding_stage, stage) not in forward_valid_transitions:
        raise OnboardingResponses.INVALID_TRANSITION
    user.onboarding_stage = stage


@router.put(
    "/onboarding/stages/community-choice/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=OnboardingResponses.responses(),
    summary="Proceed to the community choice onboarding stage",
)
async def proceed_to_community_choice(
    user: AuthorizedUser,
    stage_data: CommunityChoiceSchema,
) -> None:
    await make_onboarding_transition(user, OnboardingStage.COMMUNITY_CHOICE)
    user.update(**stage_data.model_dump())


@router.put(
    "/onboarding/stages/{stage}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=OnboardingResponses.responses(),
    summary="Proceed to the specified onboarding stage",
)
async def proceed_to_specified_stage(
    user: AuthorizedUser,
    stage: ValidForwardStages,
) -> None:
    await make_onboarding_transition(user, stage)


@router.delete(
    "/onboarding/stages/{stage}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=OnboardingResponses.responses(),
    summary="Return to the previous onboarding stage",
)
async def return_to_previous_onboarding_stage(
    user: AuthorizedUser,
    stage: ValidReturnStages,
) -> None:
    if stage is not user.onboarding_stage:
        raise OnboardingResponses.INVALID_TRANSITION
    user.onboarding_stage = return_transitions[stage]
