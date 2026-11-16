from app.common.schemas import pochta_sch
from app.pochta.schemas.unisender_go_sch import (
    UnisenderGoSendEmailSuccessfulResponseSchema,
)
from tests.common.polyfactory_ext import BaseModelFactory


class TokenEmailMessagePayloadFactory(
    BaseModelFactory[pochta_sch.TokenEmailMessagePayloadSchema]
):
    __model__ = pochta_sch.TokenEmailMessagePayloadSchema


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
