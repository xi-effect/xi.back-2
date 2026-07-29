from pydantic import BaseModel


class BaseMetadataSchema(BaseModel):
    def model_dump_metadata_json(self) -> str:
        return self.model_dump_json(exclude_none=True)


class RoomMetadataSchema(BaseMetadataSchema):
    active_material_id: int | None = None


class ParticipantMetadataSchema(BaseMetadataSchema):
    is_hand_raised: bool = False


class ConferenceParticipantSchema(BaseModel):
    user_id: int
    display_name: str
