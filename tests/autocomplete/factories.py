from app.autocomplete.models.subjects_db import Subject
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class SubjectInputFactory(BaseModelFactory[Subject.InputSchema]):
    __model__ = Subject.InputSchema


class SubjectInputMUBFactory(BaseModelFactory[Subject.InputMUBSchema]):
    __model__ = Subject.InputMUBSchema


class SubjectPatchMUBFactory(BasePatchModelFactory[Subject.PatchMUBSchema]):
    __model__ = Subject.PatchMUBSchema
