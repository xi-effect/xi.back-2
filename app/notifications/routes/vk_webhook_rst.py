from typing import assert_never

from fastapi import HTTPException, Response
from starlette import status

from app.common.config import settings
from app.common.dependencies.webhooks_dep import WebhookTokenResponses
from app.common.fastapi_ext import APIRouterExt
from app.notifications import texts
from app.notifications.config import vk_app, vk_connection_key_provider
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    VKDeliveryMethod,
)
from app.notifications.schemas.vk.vk_messages_sch import (
    MessageSendInputSchema,
    MessageSendResponseItemSchema,
)
from app.notifications.schemas.vk.vk_updates_sch import (
    AllowMessagesUpdateSchema,
    ConfirmationUpdateSchema,
    DenyMessagesUpdateSchema,
    UpdateSchema,
)
from app.notifications.utils.deep_links import DeepLinkException

router = APIRouterExt()


class SendMessageException(Exception):
    pass


class UnexpectedMessageCountException(SendMessageException):
    def __init__(self, messages: list[MessageSendResponseItemSchema]) -> None:
        self.messages = messages


class MessageDeliveryFailedException(SendMessageException):
    def __init__(self, message: MessageSendResponseItemSchema) -> None:
        self.message = message


class MessageReceiverMismatchException(SendMessageException):
    def __init__(
        self,
        message: MessageSendResponseItemSchema,
        expected_peer_id: int,
    ) -> None:
        self.message = message
        self.expected_peer_id = expected_peer_id


async def reply_with_text(peer_id: int, text: str) -> MessageSendResponseItemSchema:
    messages = await vk_app.client.send_message(
        data=MessageSendInputSchema(
            peer_ids=[peer_id],
            message=text,
        )
    )

    if len(messages) != 1:
        raise UnexpectedMessageCountException(messages=messages)

    message = messages[0]

    if message.error is not None:
        # TODO: `message.error.code == 901` means the bot is blocked
        raise MessageDeliveryFailedException(message=message)

    if message.peer_id != peer_id:
        raise MessageReceiverMismatchException(
            message=message,
            expected_peer_id=peer_id,
        )

    return message


async def reactivate_existing_delivery_method(
    delivery_method: VKDeliveryMethod,
) -> None:
    if delivery_method.status is DeliveryMethodStatus.BLOCKED:
        delivery_method.status = DeliveryMethodStatus.ACTIVE
        # TODO update vk contact for `user_id`
        await reply_with_text(
            peer_id=delivery_method.peer_id,
            text=texts.NOTIFICATIONS_RECONNECTED_MESSAGE,
        )


async def handle_unbanning(peer_id: int) -> None:
    current_delivery_method = await VKDeliveryMethod.find_first_by_peer_id_and_status(
        peer_id=peer_id,
        allowed_statuses=[
            DeliveryMethodStatus.ACTIVE,
            DeliveryMethodStatus.BLOCKED,
        ],
    )
    if current_delivery_method is None:
        await reply_with_text(
            peer_id=peer_id,
            text=texts.START_WITHOUT_DEEP_LINK_MESSAGE,
        )
        return

    await reactivate_existing_delivery_method(current_delivery_method)


async def handle_allow_messages(update: AllowMessagesUpdateSchema) -> None:
    peer_id = update.object.user_id

    if update.object.key == "":
        await handle_unbanning(peer_id)
        return

    try:
        user_id = vk_connection_key_provider.verify_and_decode_signed_link_payload(
            link_payload=update.object.key
        )
    except DeepLinkException:
        await reply_with_text(peer_id=peer_id, text=texts.INVALID_TOKEN_MESSAGE)
        return

    current_delivery_method = await VKDeliveryMethod.find_first_by_user_id(
        user_id=user_id
    )

    if current_delivery_method is not None:
        if current_delivery_method.peer_id != peer_id:
            await reply_with_text(
                peer_id=peer_id,
                text=texts.TOKEN_ALREADY_USED_MESSAGE,
            )
            return

        await reactivate_existing_delivery_method(current_delivery_method)
        return

    delivery_method_to_replace = (
        await VKDeliveryMethod.find_first_by_peer_id_and_status(
            peer_id=peer_id,
            allowed_statuses=[
                DeliveryMethodStatus.ACTIVE,
                DeliveryMethodStatus.BLOCKED,
            ],
        )
    )
    if delivery_method_to_replace is None:
        is_replacing_another_connection = False
    else:
        delivery_method_to_replace.status = DeliveryMethodStatus.REPLACED
        # TODO remove vk contact for `delivery_method.user_id`
        # TODO notify user on-platform (& email?) about the connection replacement
        is_replacing_another_connection = True

    await VKDeliveryMethod.create(
        user_id=user_id,
        peer_id=peer_id,
        status=DeliveryMethodStatus.ACTIVE,
    )
    # TODO update vk contact for `user_id`

    await reply_with_text(
        peer_id=peer_id,
        text=(
            texts.NOTIFICATIONS_REPLACES_MESSAGE
            if is_replacing_another_connection
            else texts.NOTIFICATIONS_CONNECTED_MESSAGE
        ),
    )


async def handle_deny_messages(update: DenyMessagesUpdateSchema) -> None:
    peer_id = update.object.user_id

    delivery_method = await VKDeliveryMethod.find_first_by_peer_id_and_status(
        peer_id=peer_id,
        allowed_statuses=[DeliveryMethodStatus.ACTIVE],
    )

    if delivery_method is None:
        return

    delivery_method.status = DeliveryMethodStatus.BLOCKED
    # TODO remove vk contact for `delivery_method.user_id`


@router.post(
    path="/vk-updates/",
    responses=WebhookTokenResponses.responses(),
    summary="Execute VK webhook for notifications bot",
)
async def handle_update_from_vk(update: UpdateSchema) -> Response:
    if settings.vk_notifications_bot is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Notifications bot configuration is missing",
        )

    if (
        settings.vk_notifications_bot.webhook_secret_key is not None
        and update.secret != settings.vk_notifications_bot.webhook_secret_key
    ):
        raise WebhookTokenResponses.INVALID_WEBHOOK_TOKEN

    match update:
        case ConfirmationUpdateSchema():
            return Response(
                content=settings.vk_notifications_bot.confirmation_code,
                media_type="text/plain",
            )
        case AllowMessagesUpdateSchema():
            await handle_allow_messages(update)
        case DenyMessagesUpdateSchema():
            await handle_deny_messages(update)
        case _:
            assert_never(update)

    return Response(content="ok", media_type="text/plain")
