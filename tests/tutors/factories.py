from app.tutors.models.materials_db import Material
from app.tutors.models.subjects_db import Subject
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class SubjectInputFactory(BaseModelFactory[Subject.InputSchema]):
    __model__ = Subject.InputSchema


class SubjectInputMUBFactory(BaseModelFactory[Subject.InputMUBSchema]):
    __model__ = Subject.InputMUBSchema


class SubjectPatchMUBFactory(BasePatchModelFactory[Subject.PatchMUBSchema]):
    __model__ = Subject.PatchMUBSchema


class MaterialInputFactory(BaseModelFactory[Material.InputSchema]):
    __model__ = Material.InputSchema


class MaterialPatchFactory(BasePatchModelFactory[Material.PatchSchema]):
    __model__ = Material.PatchSchema
