from polyfactory import Use
from pydantic import BaseModel

from app.common.schemas.pochta_sch import (
    ClassroomNotificationEmailMessagePayloadSchema,
    CustomEmailMessagePayloadSchema,
    EmailMessageInputSchema,
    RecipientInvoiceNotificationEmailMessagePayloadSchema,
    TokenEmailMessagePayloadSchema,
)
from app.pochta.schemas.unisender_go_sch import (
    UnisenderGoSendEmailSuccessfulResponseSchema,
)
from tests.common.polyfactory_ext import BaseModelFactory


class EmailFormDataSchema(BaseModel):
    receiver: str
    subject: str


class EmailFormDataFactory(BaseModelFactory[EmailFormDataSchema]):
    __model__ = EmailFormDataSchema

    receiver = Use(BaseModelFactory.__faker__.email)
    subject = Use(BaseModelFactory.__faker__.sentence)


class CustomEmailMessagePayloadFactory(
    BaseModelFactory[CustomEmailMessagePayloadSchema]
):
    __model__ = CustomEmailMessagePayloadSchema


class TokenEmailMessagePayloadFactory(BaseModelFactory[TokenEmailMessagePayloadSchema]):
    __model__ = TokenEmailMessagePayloadSchema


class ClassroomNotificationEmailMessagePayloadFactory(
    BaseModelFactory[ClassroomNotificationEmailMessagePayloadSchema]
):
    __model__ = ClassroomNotificationEmailMessagePayloadSchema


class RecipientInvoiceNotificationEmailMessagePayloadFactory(
    BaseModelFactory[RecipientInvoiceNotificationEmailMessagePayloadSchema]
):
    __model__ = RecipientInvoiceNotificationEmailMessagePayloadSchema


class EmailMessageInputFactory(BaseModelFactory[EmailMessageInputSchema]):
    __model__ = EmailMessageInputSchema


class UnisenderGoSendEmailSuccessfulResponseFactory(
    BaseModelFactory[UnisenderGoSendEmailSuccessfulResponseSchema]
):
    __model__ = UnisenderGoSendEmailSuccessfulResponseSchema
