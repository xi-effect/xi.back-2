from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas.content_sch import YDocContentKind


class BaseMetadataSchema(BaseModel):
    def model_dump_metadata_json(self) -> str:
        return self.model_dump_json(exclude_none=True)


class ActiveMaterialSchema(BaseModel):
    id: UUID
    content_kind: YDocContentKind


class RoomMetadataSchema(BaseMetadataSchema):
    active_material_id: int | None = Field(None, deprecated=True)
    active_material: ActiveMaterialSchema | None = None


class ParticipantMetadataSchema(BaseMetadataSchema):
    is_hand_raised: bool = False


class ConferenceParticipantSchema(BaseModel):
    user_id: int
    display_name: str
