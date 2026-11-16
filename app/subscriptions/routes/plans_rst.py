from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.subscriptions_sch import PlanSchema
from app.subscriptions.services import plans_svc

router = APIRouterExt(tags=["plans"])


@router.get(
    path="/users/current/plan/",
    summary="Retrieve current user's plan",
)
async def retrieve_current_plan(auth_data: AuthorizationData) -> PlanSchema:
    return await plans_svc.retrieve_plan_by_user_id(user_id=auth_data.user_id)
