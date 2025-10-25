from app.common.schemas.storage_sch import StorageTokenPayloadSchema
from tests.common.polyfactory_ext import BaseModelFactory


class StorageTokenPayloadFactory(BaseModelFactory[StorageTokenPayloadSchema]):
    __model__ = StorageTokenPayloadSchema
