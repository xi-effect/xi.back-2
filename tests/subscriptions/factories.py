from datetime import timezone

from polyfactory import PostGenerated, Require, Use
from pydantic import AwareDatetime, BaseModel

from app.common.pydantic_ext import FutureAwareDatetime, PastAwareDatetime
from app.common.schemas.subscriptions_sch import PaidPlanKind
from app.subscriptions.models.promocodes_db import Promocode, promocode_code_generator
from app.subscriptions.routes.promocodes_mub import (
    PromocodeBatchGenerationRequestSchema,
)
from app.subscriptions.schemas.subscriptions_sch import SubscriptionPeriod
from app.subscriptions.schemas.yookassa_sch import (
    YooKassaCanceledPaymentSchema,
    YooKassaEventObjectSchema,
    YooKassaEventSchema,
    YooKassaPaymentMethodSchema,
    YooKassaPendingPaymentSchema,
    YooKassaSucceededPaymentSchema,
    YooKassaWaitingForCapturePaymentSchema,
)
from tests.common.polyfactory_ext import BaseModelFactory


class SubscriptionInputSchema(BaseModel):
    plan_kind: PaidPlanKind
    ends_at: AwareDatetime


class ActiveSubscriptionInputSchema(SubscriptionInputSchema):
    ends_at: FutureAwareDatetime


class ActiveSubscriptionInputFactory(BaseModelFactory[ActiveSubscriptionInputSchema]):
    __model__ = ActiveSubscriptionInputSchema


class ExpiredSubscriptionInputSchema(SubscriptionInputSchema):
    ends_at: PastAwareDatetime


class ExpiredSubscriptionInputFactory(BaseModelFactory[ExpiredSubscriptionInputSchema]):
    __model__ = ExpiredSubscriptionInputSchema


class AutoRenewalInputSchema(BaseModel):
    provider_payment_method_id: str
    renewal_period: SubscriptionPeriod


class AutoRenewalInputFactory(BaseModelFactory[AutoRenewalInputSchema]):
    __model__ = AutoRenewalInputSchema

    provider_payment_method_id = Use(BaseModelFactory.__faker__.uuid4)


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


class StoredPaymentInputSchema(BaseModel):
    provider_payment_id: str
    amount_roubles: int
    subscription_days: int


class StoredPaymentInputFactory(BaseModelFactory[StoredPaymentInputSchema]):
    __model__ = StoredPaymentInputSchema

    provider_payment_id = Use(BaseModelFactory.__faker__.uuid4)


class YooKassaPendingPaymentFactory(BaseModelFactory[YooKassaPendingPaymentSchema]):
    __model__ = YooKassaPendingPaymentSchema


class YooKassaWaitingForCapturePaymentFactory(
    BaseModelFactory[YooKassaWaitingForCapturePaymentSchema]
):
    __model__ = YooKassaWaitingForCapturePaymentSchema


class YooKassaPaymentMethodFactory(BaseModelFactory[YooKassaPaymentMethodSchema]):
    __model__ = YooKassaPaymentMethodSchema

    id = Use(BaseModelFactory.__faker__.uuid4)


class YooKassaSucceededPaymentFactory(BaseModelFactory[YooKassaSucceededPaymentSchema]):
    __model__ = YooKassaSucceededPaymentSchema


class YooKassaCanceledPaymentFactory(BaseModelFactory[YooKassaCanceledPaymentSchema]):
    __model__ = YooKassaCanceledPaymentSchema


class YooKassaEventObjectFactory(BaseModelFactory[YooKassaEventObjectSchema]):
    __model__ = YooKassaEventObjectSchema


class YooKassaEventFactory(BaseModelFactory[YooKassaEventSchema]):
    __model__ = YooKassaEventSchema
