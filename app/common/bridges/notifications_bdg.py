from httpx import Response
from pydantic import TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.config import settings
from app.common.schemas.notifications_sch import (
    DeliveryMethodKind,
    NotificationInputV2Schema,
)
from app.common.schemas.user_contacts_sch import UserContactSchema

user_contact_list_type_adapter = TypeAdapter(list[UserContactSchema])


class NotificationsBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/notification-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def list_user_contacts(
        self,
        user_id: int,
        public_only: bool = False,
    ) -> list[UserContactSchema]:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(
                    f"/users/{user_id}/contacts/",
                    params={"public_only": public_only},
                )
            )
            .validate_status_code()
            .validate_json(user_contact_list_type_adapter)
        )

    async def create_or_update_email_delivery_method(
        self,
        user_id: int,
        email: str,
    ) -> Response:
        return await ResponsePipelineBuilder.initialize_from_request(
            self.client.put(
                f"/users/{user_id}/delivery-methods/{DeliveryMethodKind.EMAIL}/",
                json={"email": email},
            )
        ).validate_status_code()

    async def send_notification(
        self,
        data: NotificationInputV2Schema,
    ) -> None:
        await self.broker.publish(
            message=data.model_dump(mode="json"),
            stream=settings.notifications_send_stream_name,
        )
