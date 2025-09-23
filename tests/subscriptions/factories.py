from datetime import timezone

from polyfactory import PostGenerated
from pydantic import AwareDatetime

from app.subscriptions.models.promocodes_db import Promocode
from tests.common.polyfactory_ext import BaseModelFactory


class PromocodeInputSchema(Promocode.InputSchema):
    valid_from: AwareDatetime
    valid_until: AwareDatetime


class LimitedPromocodeInputFactory(BaseModelFactory[PromocodeInputSchema]):
    __model__ = PromocodeInputSchema

    valid_until = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time_between(
            start_date=values["valid_from"], tzinfo=timezone.utc
        )
    )


class UnlimitedPromocodeInputFactory(BaseModelFactory[Promocode.InputSchema]):
    __model__ = Promocode.InputSchema

    valid_from = None
    valid_until = None


class InvalidPeriodPromocodeInputFactory(BaseModelFactory[PromocodeInputSchema]):
    __model__ = PromocodeInputSchema

    valid_from = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time_between(
            start_date=values["valid_until"], tzinfo=timezone.utc
        )
    )
