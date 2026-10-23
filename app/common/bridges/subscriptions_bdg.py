from pydantic import TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.config import settings
from app.common.schemas.subscriptions_sch import PlanSchema, UserPlanUpdateEventSchema

plan_type_adapter = TypeAdapter(PlanSchema)


class SubscriptionsBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/subscription-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def retrieve_user_plan(self, user_id: int) -> PlanSchema:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(f"/users/{user_id}/plan/")
            )
            .validate_status_code()
            .validate_json(plan_type_adapter)
        )

    async def publish_user_plan_update(self, data: UserPlanUpdateEventSchema) -> None:
        await self.broker.publish(  # TODO (302) pragma: no cover
            message=data.model_dump(mode="json"),
            stream=settings.user_plans_updated_stream_name,
        )
