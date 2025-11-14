from polyfactory import Use
from pydantic import BaseModel

from app.common.schemas.pochta_sch import EmailMessageInputSchema
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


class EmailMessageInputFactory(BaseModelFactory[EmailMessageInputSchema]):
    __model__ = EmailMessageInputSchema

    recipient_email = Use(BaseModelFactory.__faker__.email)


class UnisenderGoSendEmailSuccessfulResponseFactory(
    BaseModelFactory[UnisenderGoSendEmailSuccessfulResponseSchema]
):
    __model__ = UnisenderGoSendEmailSuccessfulResponseSchema
