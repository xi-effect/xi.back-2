from pydantic import BaseModel

from app.classrooms.models.classrooms_db import (
    GroupClassroom,
    IndividualClassroom,
    UserClassroomStatus,
)
from app.classrooms.models.materials_db import Material
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


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
