from collections import defaultdict
from collections.abc import Sequence

from aiogram.utils.deep_linking import create_deep_link
from pydantic import BaseModel, ConfigDict
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.config import (
    telegram_app,
    telegram_deep_link_provider,
    vk_app,
    vk_connection_key_provider,
)
from app.notifications.dependencies.delivery_methods_dep import (
    MissingTelegramDeliveryMethodDep,
    MissingVKDeliveryMethodDep,
    MyEditableDeliveryMethodByKind,
)
from app.notifications.models.delivery_methods_db import (
    DeliveryMethod,
    EmailDeliveryMethod,
    TelegramDeliveryMethod,
    VKDeliveryMethod,
)
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services import user_contacts_svc

router = APIRouterExt(tags=["delivery methods"])


# Using pre-schemas because of a bug in `CompositeMarshalModel`
# https://github.com/niqzart/pydantic-marshals/issues/38


class DeliveryMethodEnrichedPreSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    delivery_method: DeliveryMethod
    related_contact: UserContact | None
    enabled_notification_categories: set[NotificationCategory]


class DeliveryMethodsResponsePreSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    email: DeliveryMethodEnrichedPreSchema | None
    telegram: DeliveryMethodEnrichedPreSchema | None
    vk: DeliveryMethodEnrichedPreSchema | None


class DeliveryMethodEnrichedSchema[DeliveryMethodSchema: BaseModel](BaseModel):
    delivery_method: DeliveryMethodSchema
    related_contact: UserContact.ResponseSchema | None
    enabled_notification_categories: list[NotificationCategory]


class DeliveryMethodsResponseSchema(BaseModel):
    email: DeliveryMethodEnrichedSchema[EmailDeliveryMethod.ResponseSchema] | None
    telegram: DeliveryMethodEnrichedSchema[TelegramDeliveryMethod.ResponseSchema] | None
    vk: DeliveryMethodEnrichedSchema[VKDeliveryMethod.ResponseSchema] | None


USER_CONTACT_KIND_TO_DELIVERY_METHOD_KIND: dict[UserContactKind, DeliveryMethodKind] = {
    UserContactKind.PERSONAL_TELEGRAM: DeliveryMethodKind.TELEGRAM,
    UserContactKind.PERSONAL_VK: DeliveryMethodKind.VK,
}


class DeliveryMethodsSchemaAdapter:
    def __init__(
        self,
        delivery_methods: Sequence[DeliveryMethod],
        user_contacts: Sequence[UserContact],
        disabled_delivery_routes: Sequence[DisabledDeliveryRoute],
    ) -> None:
        self.delivery_methods_by_kind = {
            delivery_method.kind: delivery_method
            for delivery_method in delivery_methods
        }
        self.user_contacts_by_delivery_method_kind = {
            USER_CONTACT_KIND_TO_DELIVERY_METHOD_KIND[user_contact.kind]: user_contact
            for user_contact in user_contacts
        }
        self.enabled_notification_categories_by_delivery_method_kind: dict[
            DeliveryMethodKind, set[NotificationCategory]
        ] = defaultdict(lambda: set(NotificationCategory))
        for disabled_delivery_route in disabled_delivery_routes:
            self.enabled_notification_categories_by_delivery_method_kind[
                disabled_delivery_route.delivery_method_kind
            ].remove(disabled_delivery_route.notification_category)

    def adapt_delivery_method(
        self,
        delivery_method_kind: DeliveryMethodKind,
    ) -> DeliveryMethodEnrichedPreSchema | None:
        delivery_method = self.delivery_methods_by_kind.get(delivery_method_kind)
        if delivery_method is None:
            return None
        return DeliveryMethodEnrichedPreSchema(
            delivery_method=delivery_method,
            related_contact=self.user_contacts_by_delivery_method_kind.get(
                delivery_method_kind
            ),
            enabled_notification_categories=(
                self.enabled_notification_categories_by_delivery_method_kind[
                    delivery_method_kind
                ]
            ),
        )

    def adapt(self) -> DeliveryMethodsResponsePreSchema:
        return DeliveryMethodsResponsePreSchema(
            email=self.adapt_delivery_method(DeliveryMethodKind.EMAIL),
            telegram=self.adapt_delivery_method(DeliveryMethodKind.TELEGRAM),
            vk=self.adapt_delivery_method(DeliveryMethodKind.VK),
        )


@router.get(
    path="/users/current/delivery-methods/",
    response_model=DeliveryMethodsResponseSchema,
    summary="Retrieve all available delivery methods for the current user",
)
async def retrieve_all_delivery_methods(
    auth_data: AuthorizationData,
) -> DeliveryMethodsResponsePreSchema:
    adapter = DeliveryMethodsSchemaAdapter(
        delivery_methods=await DeliveryMethod.find_all_by_user_id(
            user_id=auth_data.user_id,
        ),
        user_contacts=await UserContact.find_all_by_user_id_and_kinds(
            user_id=auth_data.user_id,
            allowed_kinds=USER_CONTACT_KIND_TO_DELIVERY_METHOD_KIND.keys(),
        ),
        disabled_delivery_routes=await DisabledDeliveryRoute.find_all_by_user_id(
            user_id=auth_data.user_id,
        ),
    )
    return adapter.adapt()


@router.post(
    path=f"/users/current/delivery-methods/{DeliveryMethodKind.TELEGRAM}/connection-requests/",
    dependencies=[MissingTelegramDeliveryMethodDep],
    summary="Generate a link for connecting telegram notifications for the current user",
)
async def generate_telegram_connection_link(auth_data: AuthorizationData) -> str:
    return create_deep_link(
        username=telegram_app.bot_username,
        link_type="start",
        payload=telegram_deep_link_provider.create_signed_link_payload(
            user_id=auth_data.user_id,
        ),
    )


class VKConnectionStartResponseSchema(BaseModel):
    group_id: int
    key: str


@router.post(
    path=f"/users/current/delivery-methods/{DeliveryMethodKind.VK}/connection-requests/",
    dependencies=[MissingVKDeliveryMethodDep],
    summary="Generate data for connecting vk notifications for the current user",
)
async def generate_vk_connection_data(
    auth_data: AuthorizationData,
) -> VKConnectionStartResponseSchema:
    return VKConnectionStartResponseSchema(
        group_id=vk_app.client.group_id,
        key=vk_connection_key_provider.create_signed_link_payload(
            user_id=auth_data.user_id,
        ),
    )


@router.delete(
    path="/users/current/delivery-methods/{delivery_method_kind}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any delivery method by kind for the current user",
)
async def delete_delivery_method(
    delivery_method: MyEditableDeliveryMethodByKind,
) -> None:
    await delivery_method.delete()

    # TODO implement user contacts for VK  # TODO nq not this weekend tho
    if delivery_method.kind is DeliveryMethodKind.TELEGRAM:
        await user_contacts_svc.remove_personal_telegram_contact(
            user_id=delivery_method.user_id
        )
