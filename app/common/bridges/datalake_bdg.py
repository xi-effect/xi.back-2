from app.common.bridges.base_bdg import BaseBridge
from app.common.config import settings
from app.common.schemas.datalake_sch import DatalakeEventInputSchema


class DatalakeBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/datalake-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def record_datalake_event(self, data: DatalakeEventInputSchema) -> None:
        await self.broker.publish(
            message=data.model_dump(mode="json"),
            stream=settings.datalake_events_record_stream_name,
        )
