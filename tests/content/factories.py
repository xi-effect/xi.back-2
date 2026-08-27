from app.common.schemas.content_sch import ContentTokenPayloadSchema
from app.content.models.materials_db import ClassroomMaterial, PersonalMaterial
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class ContentTokenPayloadFactory(BaseModelFactory[ContentTokenPayloadSchema]):
    __model__ = ContentTokenPayloadSchema


class PersonalMaterialInputFactory(BaseModelFactory[PersonalMaterial.InputSchema]):
    __model__ = PersonalMaterial.InputSchema


class PersonalMaterialPatchFactory(BasePatchModelFactory[PersonalMaterial.PatchSchema]):
    __model__ = PersonalMaterial.PatchSchema


class ClassroomMaterialInputFactory(BaseModelFactory[ClassroomMaterial.InputSchema]):
    __model__ = ClassroomMaterial.InputSchema


class ClassroomMaterialDuplicateInputFactory(
    BaseModelFactory[ClassroomMaterial.DuplicateInputSchema]
):
    __model__ = ClassroomMaterial.DuplicateInputSchema


class ClassroomMaterialPatchFactory(
    BasePatchModelFactory[ClassroomMaterial.PatchSchema]
):
    __model__ = ClassroomMaterial.PatchSchema
