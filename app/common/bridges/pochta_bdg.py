from app.common.bridges.base_bdg import BaseBridge
from app.common.config import settings
from app.common.schemas.pochta_sch import EmailMessageInputSchema


class PochtaBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/pochta-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def send_email_message(self, data: EmailMessageInputSchema) -> None:
        await self.broker.publish(
            message=data.model_dump(mode="json"),
            stream=settings.email_messages_send_stream_name,
        )
