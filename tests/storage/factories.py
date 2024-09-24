from app.storage.models.access_groups_db import AccessGroup
from tests.common.polyfactory_ext import BaseModelFactory


class AccessGroupInputFactory(BaseModelFactory[AccessGroup.InputSchema]):
    __model__ = AccessGroup.InputSchema
