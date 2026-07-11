from collections.abc import Sequence
from typing import Literal

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
)
from app.notifications.dependencies.delivery_methods_dep import (
    MissingTelegramDeliveryMethodDep,
    MyDeliveryMethodByKind,
)
from app.notifications.models.delivery_methods_db import (
    DeliveryMethod,
    EmailDeliveryMethod,
    TelegramDeliveryMethod,
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


class DeliveryMethodsResponsePreSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    email: DeliveryMethodEnrichedPreSchema | None
    telegram: DeliveryMethodEnrichedPreSchema | None


class DeliveryMethodEnrichedSchema[DeliveryMethodSchema: BaseModel](BaseModel):
    delivery_method: DeliveryMethodSchema
    related_contact: UserContact.ResponseSchema | None


class DeliveryMethodsResponseSchema(BaseModel):
    email: DeliveryMethodEnrichedSchema[EmailDeliveryMethod.ResponseSchema] | None
    telegram: DeliveryMethodEnrichedSchema[TelegramDeliveryMethod.ResponseSchema] | None


USER_CONTACT_KIND_TO_DELIVERY_METHOD_KIND: dict[UserContactKind, DeliveryMethodKind] = {
    UserContactKind.PERSONAL_TELEGRAM: DeliveryMethodKind.TELEGRAM,
}


class DeliveryMethodsSchemaAdapter:
    def __init__(
        self,
        delivery_methods: Sequence[DeliveryMethod],
        user_contacts: Sequence[UserContact],
    ) -> None:
        self.delivery_methods_by_kind = {
            delivery_method.kind: delivery_method
            for delivery_method in delivery_methods
        }
        self.user_contacts_by_delivery_method_kind = {
            USER_CONTACT_KIND_TO_DELIVERY_METHOD_KIND[user_contact.kind]: user_contact
            for user_contact in user_contacts
        }

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
        )

    def adapt(self) -> DeliveryMethodsResponsePreSchema:
        return DeliveryMethodsResponsePreSchema(
            email=self.adapt_delivery_method(DeliveryMethodKind.EMAIL),
            telegram=self.adapt_delivery_method(DeliveryMethodKind.TELEGRAM),
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


DeletableDeliveryMethodKind = Literal[DeliveryMethodKind.TELEGRAM]


@router.delete(
    path="/users/current/delivery-methods/{delivery_method_kind}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any delivery method by kind for the current user",
)
async def delete_delivery_method(delivery_method: MyDeliveryMethodByKind) -> None:
    await delivery_method.delete()
    await user_contacts_svc.remove_personal_telegram_contact(
        user_id=delivery_method.user_id
    )  # TODO redo for vk
