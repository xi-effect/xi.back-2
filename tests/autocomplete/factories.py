from app.autocomplete.models.tags_db import Tag
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class TagInputFactory(BaseModelFactory[Tag.InputSchema]):
    __model__ = Tag.InputSchema


class TagInputMUBFactory(BaseModelFactory[Tag.InputMUBSchema]):
    __model__ = Tag.InputMUBSchema


class TagPatchMUBFactory(BasePatchModelFactory[Tag.PatchMUBSchema]):
    __model__ = Tag.PatchMUBSchema
