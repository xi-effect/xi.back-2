from typing import Annotated

from fastapi import Path

from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.subscriptions_sch import PlanSchema
from app.subscriptions.services import plans_svc

router = APIRouterExt(tags=["plans internal"])


@router.get(
    path="/users/{user_id}/plan/",
    summary="Retrieve user's plan by id",
)
async def retrieve_user_plan(user_id: Annotated[int, Path()]) -> PlanSchema:
    return await plans_svc.retrieve_plan_by_user_id(user_id=user_id)
