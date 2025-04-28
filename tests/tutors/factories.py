from app.tutors.models.materials_db import Material
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class MaterialInputFactory(BaseModelFactory[Material.InputSchema]):
    __model__ = Material.InputSchema


class MaterialPatchFactory(BasePatchModelFactory[Material.PatchSchema]):
    __model__ = Material.PatchSchema
