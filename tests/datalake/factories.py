from app.common.schemas.datalake_sch import DatalakeEventInputSchema
from tests.common.polyfactory_ext import BaseModelFactory


class DatalakeEventInputFactory(BaseModelFactory[DatalakeEventInputSchema]):
    __model__ = DatalakeEventInputSchema
