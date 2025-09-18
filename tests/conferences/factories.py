from app.conferences.schemas.conferences_sch import ConferenceParticipantSchema
from tests.common.polyfactory_ext import BaseModelFactory


class ConferenceParticipantFactory(BaseModelFactory[ConferenceParticipantSchema]):
    __model__ = ConferenceParticipantSchema
