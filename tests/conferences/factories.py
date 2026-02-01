from app.conferences.schemas.conferences_sch import (
    ConferenceParticipantSchema,
    RoomMetadataSchema,
)
from tests.common.polyfactory_ext import BaseModelFactory


class RoomMetadataFactory(BaseModelFactory[RoomMetadataSchema]):
    __model__ = RoomMetadataSchema


class ConferenceParticipantFactory(BaseModelFactory[ConferenceParticipantSchema]):
    __model__ = ConferenceParticipantSchema
