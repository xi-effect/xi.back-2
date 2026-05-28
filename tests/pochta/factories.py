from polyfactory import Use
from pydantic import BaseModel

from app.common.schemas import pochta_sch
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
    BaseModelFactory[pochta_sch.CustomEmailMessagePayloadSchema]
):
    __model__ = pochta_sch.CustomEmailMessagePayloadSchema


class TokenEmailMessagePayloadFactory(
    BaseModelFactory[pochta_sch.TokenEmailMessagePayloadSchema]
):
    __model__ = pochta_sch.TokenEmailMessagePayloadSchema


class ClassroomNotificationEmailMessagePayloadFactory(
    BaseModelFactory[pochta_sch.ClassroomNotificationEmailMessagePayloadSchema]
):
    __model__ = pochta_sch.ClassroomNotificationEmailMessagePayloadSchema


class RecipientInvoiceNotificationEmailMessagePayloadFactory(
    BaseModelFactory[pochta_sch.RecipientInvoiceNotificationEmailMessagePayloadSchema]
):
    __model__ = pochta_sch.RecipientInvoiceNotificationEmailMessagePayloadSchema


class UniversalEmailMessagePayloadFactory(
    BaseModelFactory[pochta_sch.UniversalEmailMessagePayloadSchema]
):
    __model__ = pochta_sch.UniversalEmailMessagePayloadSchema


class EmailMessageInputFactory(BaseModelFactory[pochta_sch.EmailMessageInputSchema]):
    __model__ = pochta_sch.EmailMessageInputSchema


class UnisenderGoSendEmailSuccessfulResponseFactory(
    BaseModelFactory[UnisenderGoSendEmailSuccessfulResponseSchema]
):
    __model__ = UnisenderGoSendEmailSuccessfulResponseSchema
