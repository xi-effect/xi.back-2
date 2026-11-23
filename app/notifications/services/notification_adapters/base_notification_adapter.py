from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlencode

from pydantic import BaseModel

from app.common.config import settings
from app.common.schemas.pochta_sch import UniversalEmailMessagePayloadSchema
from app.notifications.models.notifications_db import Notification


class MessengerMessagePayloadSchema(BaseModel):
    message_text: str
    button_text: str
    button_link: str


class BaseNotificationAdapter[PayloadType](ABC):
    def __init__(self, notification: Notification, payload: PayloadType) -> None:
        self.notification = notification
        self.payload = payload

    def build_url(self, path: str, params: dict[str, Any]) -> str:
        query_string = urlencode(
            {
                **params,
                "read_notification_id": self.notification.id,
                # TODO (199) maybe add "role": "student|tutor",
            }
        )
        return f"{settings.frontend_app_base_url}{path}?{query_string}"

    @abstractmethod
    def adapt_button_text(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def adapt_button_link(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def adapt_message_text(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def adapt_email_theme(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def adapt_email_pre_header(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def adapt_email_header(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def adapt_email_content(self) -> str:
        raise NotImplementedError

    def to_messenger_message_payload(self) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=self.adapt_message_text(),
            button_text=self.adapt_button_text(),
            button_link=self.adapt_button_link(),
        )

    def to_universal_email_message_payload(
        self,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=self.adapt_email_theme(),
            pre_header=self.adapt_email_pre_header(),
            header=self.adapt_email_header(),
            content=self.adapt_email_content(),
            button_text=self.adapt_button_text(),
            button_link=self.adapt_button_link(),
        )
