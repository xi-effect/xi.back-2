from pydantic import BaseModel


class ConferenceParticipantSchema(BaseModel):
    user_id: int
    display_name: str
