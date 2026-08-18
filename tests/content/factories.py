from app.common.schemas.content_sch import ContentTokenPayloadSchema
from tests.common.polyfactory_ext import BaseModelFactory


class ContentTokenPayloadFactory(BaseModelFactory[ContentTokenPayloadSchema]):
    __model__ = ContentTokenPayloadSchema
