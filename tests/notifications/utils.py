from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import UUID

from pydantic import HttpUrl
from pydantic_marshals.contains import assert_contains

from app.common.config import settings
from app.common.schemas import pochta_sch
from app.notifications.services.notification_adapters.base_notification_adapter import (
    MessengerMessagePayloadSchema,
)


def assert_messenger_message_payload(
    message_payload: MessengerMessagePayloadSchema,
    expected_notification_id: UUID,
    expected_message_text: str,
    expected_button_text: str,
    expected_button_link_path: str,
    expected_button_link_query: dict[str, list[Any]],
) -> None:
    assert_contains(
        message_payload,
        {
            "message_text": expected_message_text,
            "button_text": expected_button_text,
            "button_link": HttpUrl,
        },
    )

    assert message_payload.button_link.startswith(settings.frontend_app_base_url)
    parsed_button_link = urlparse(message_payload.button_link)
    assert_contains(
        {
            "path": parsed_button_link.path,
            "query": parse_qs(parsed_button_link.query),
        },
        {
            "path": expected_button_link_path,
            "query": {
                **expected_button_link_query,
                "read_notification_id": [expected_notification_id],
            },
        },
    )


def assert_universal_email_message_payload(
    universal_email_message_payload: pochta_sch.UniversalEmailMessagePayloadSchema,
    expected_notification_id: UUID,
    expected_theme: str,
    expected_pre_header: str,
    expected_header: str,
    expected_content: str,
    expected_button_text: str,
    expected_button_link_path: str,
    expected_button_link_query: dict[str, list[Any]],
) -> None:
    assert_contains(
        universal_email_message_payload,
        {
            "theme": expected_theme,
            "pre_header": expected_pre_header,
            "header": expected_header,
            "content": expected_content,
            "button_text": expected_button_text,
            "button_link": HttpUrl,
        },
    )

    assert universal_email_message_payload.button_link.startswith(
        settings.frontend_app_base_url,
    )
    parsed_button_link = urlparse(universal_email_message_payload.button_link)
    assert_contains(
        {
            "path": parsed_button_link.path,
            "query": parse_qs(parsed_button_link.query),
        },
        {
            "path": expected_button_link_path,
            "query": {
                **expected_button_link_query,
                "read_notification_id": [expected_notification_id],
            },
        },
    )
