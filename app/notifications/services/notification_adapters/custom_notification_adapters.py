from app.common.schemas.notifications_sch import CustomNotificationPayloadSchema
from app.notifications.services.notification_adapters.base_notification_adapter import (
    BaseNotificationAdapter,
)


class CustomV1NotificationAdapter(
    BaseNotificationAdapter[CustomNotificationPayloadSchema]
):
    def adapt_button_text(self) -> str:
        return self.payload.button_text

    def adapt_button_link(self) -> str:
        return self.payload.button_link

    def adapt_message_text(self) -> str:
        return f"{self.payload.header}\n\n{self.payload.content}"

    def adapt_email_theme(self) -> str:
        return self.payload.theme

    def adapt_email_pre_header(self) -> str:
        return self.payload.pre_header

    def adapt_email_header(self) -> str:
        return self.payload.header

    def adapt_email_content(self) -> str:
        return self.payload.content
