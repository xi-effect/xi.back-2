from polyfactory import Use
from pydantic import BaseModel

from tests.common.polyfactory_ext import BaseModelFactory


class EmailFormDataSchema(BaseModel):
    receiver: str
    subject: str


class EmailFormDataFactory(BaseModelFactory[EmailFormDataSchema]):
    __model__ = EmailFormDataSchema

    receiver = Use(BaseModelFactory.__faker__.email)
    subject = Use(BaseModelFactory.__faker__.sentence)
