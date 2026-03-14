from app.conferences.schemas.conferences_sch import (
    ConferenceParticipantSchema,
    ParticipantMetadataSchema,
    RoomMetadataSchema,
)
from tests.common.polyfactory_ext import BaseModelFactory


class RoomMetadataFactory(BaseModelFactory[RoomMetadataSchema]):
    __model__ = RoomMetadataSchema


class ParticipantMetadataFactory(BaseModelFactory[ParticipantMetadataSchema]):
    __model__ = ParticipantMetadataSchema


class ConferenceParticipantFactory(BaseModelFactory[ConferenceParticipantSchema]):
    __model__ = ConferenceParticipantSchema
