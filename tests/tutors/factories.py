from pydantic import BaseModel

from app.tutors.models.classrooms_db import (
    GroupClassroom,
    IndividualClassroom,
    UserClassroomStatus,
)
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


class IndividualClassroomInputFactory(
    BaseModelFactory[IndividualClassroom.InputSchema]
):
    __model__ = IndividualClassroom.InputSchema


class IndividualClassroomPatchFactory(
    BasePatchModelFactory[IndividualClassroom.PatchSchema]
):
    __model__ = IndividualClassroom.PatchSchema


class GroupClassroomInputFactory(BaseModelFactory[GroupClassroom.InputSchema]):
    __model__ = GroupClassroom.InputSchema


class GroupClassroomPatchFactory(BasePatchModelFactory[GroupClassroom.PatchSchema]):
    __model__ = GroupClassroom.PatchSchema


class ClassroomStatusUpdateSchema(BaseModel):
    status: UserClassroomStatus


class ClassroomStatusUpdateFactory(BaseModelFactory[ClassroomStatusUpdateSchema]):
    __model__ = ClassroomStatusUpdateSchema
