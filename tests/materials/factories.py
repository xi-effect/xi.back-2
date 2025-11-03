from app.materials.models.materials_db import ClassroomMaterial, TutorMaterial
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class TutorMaterialInputFactory(BaseModelFactory[TutorMaterial.InputSchema]):
    __model__ = TutorMaterial.InputSchema


class TutorMaterialPatchFactory(BasePatchModelFactory[TutorMaterial.PatchSchema]):
    __model__ = TutorMaterial.PatchSchema


class ClassroomMaterialInputFactory(BaseModelFactory[ClassroomMaterial.InputSchema]):
    __model__ = ClassroomMaterial.InputSchema


class ClassroomMaterialPatchFactory(
    BasePatchModelFactory[ClassroomMaterial.PatchSchema]
):
    __model__ = ClassroomMaterial.PatchSchema
