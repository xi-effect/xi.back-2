from datetime import timezone

from polyfactory import PostGenerated, Require, Use
from pydantic import AwareDatetime, BaseModel

from app.common.pydantic_ext import FutureAwareDatetime
from app.subscriptions.models.promocodes_db import Promocode, promocode_code_generator
from app.subscriptions.models.subscriptions_db import SubscriptionPlanKind
from app.subscriptions.routes.promocodes_mub import (
    PromocodeBatchGenerationRequestSchema,
)
from app.subscriptions.schemas.yookassa_sch import YooKassaPaymentResponseSchema
from tests.common.polyfactory_ext import BaseModelFactory


class SubscriptionInputSchema(BaseModel):
    plan_kind: SubscriptionPlanKind
    ends_at: FutureAwareDatetime


class SubscriptionInputFactory(BaseModelFactory[SubscriptionInputSchema]):
    __model__ = SubscriptionInputSchema


class UnlimitedPeriodPromocodeSettingsFactory(
    BaseModelFactory[Promocode.SettingsSchema]
):
    __model__ = Promocode.SettingsSchema

    valid_from = None
    valid_until = None


class PromocodeSettingsSchema(Promocode.SettingsSchema):
    valid_from: AwareDatetime
    valid_until: AwareDatetime


class LimitedPeriodPromocodeSettingsFactory(BaseModelFactory[PromocodeSettingsSchema]):
    __model__ = PromocodeSettingsSchema

    valid_until = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time_between(
            start_date=values["valid_from"], tzinfo=timezone.utc
        )
    )


class InvalidPeriodPromocodeSettingsFactory(BaseModelFactory[PromocodeSettingsSchema]):
    __model__ = PromocodeSettingsSchema

    valid_from = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time_between(
            start_date=values["valid_until"], tzinfo=timezone.utc
        )
    )


class PromocodeNoCodeInputFactory(BaseModelFactory[Promocode.InputSchema]):
    __model__ = Promocode.InputSchema

    valid_from = None
    valid_until = None
    code = None


class PromocodeWithCodeInputFactory(BaseModelFactory[Promocode.InputSchema]):
    __model__ = Promocode.InputSchema

    valid_from = None
    valid_until = None
    code = Use(promocode_code_generator.generate_token)


class PromocodeUpdateFactory(BaseModelFactory[Promocode.UpdateSchema]):
    __model__ = Promocode.UpdateSchema

    code = Use(promocode_code_generator.generate_token)


class PromocodeBatchGenerationRequestFactory(
    BaseModelFactory[PromocodeBatchGenerationRequestSchema]
):
    __model__ = PromocodeBatchGenerationRequestSchema

    settings = Require()

    @classmethod
    def title_template(cls) -> str:
        return (
            f"{cls.__faker__.pystr(min_chars=0, max_chars=20)}"
            f"{{index}}"
            f"{cls.__faker__.pystr(min_chars=0, max_chars=20)}"
        )

    @classmethod
    def batch_size(cls) -> int:
        return cls.__faker__.random_int(min=2, max=5)


class YooKassaPaymentResponseFactory(BaseModelFactory[YooKassaPaymentResponseSchema]):
    __model__ = YooKassaPaymentResponseSchema
