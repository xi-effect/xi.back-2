from datetime import timezone

from polyfactory import PostGenerated, Use
from pydantic import AwareDatetime

from app.subscriptions.models.promocodes_db import Promocode, promocode_code_generator
from tests.common.polyfactory_ext import BaseModelFactory


class UnlimitedPromocodeValidityPeriodInputFactory(BaseModelFactory[Promocode.ValidityPeriodInputSchema]):
    __model__ = Promocode.ValidityPeriodInputSchema

    valid_from = None
    valid_until = None


class PromocodeValidityPeriodInputSchema(Promocode.ValidityPeriodInputSchema):
    valid_from: AwareDatetime
    valid_until: AwareDatetime


class LimitedPromocodeValidityPeriodInputFactory(BaseModelFactory[PromocodeValidityPeriodInputSchema]):
    __model__ = PromocodeValidityPeriodInputSchema

    valid_until = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time_between(
            start_date=values["valid_from"], tzinfo=timezone.utc
        )
    )


class InvalidPromocodeValidityPeriodInputFactory(BaseModelFactory[PromocodeValidityPeriodInputSchema]):
    __model__ = PromocodeValidityPeriodInputSchema

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
