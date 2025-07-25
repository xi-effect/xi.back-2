from collections.abc import Sequence

from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.dependencies.participants_dep import ParticipantById
from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant

router = APIRouterExt(tags=["participants meta mub"])


@router.get(
    "/communities/{community_id}/participants/",
    response_model=list[Participant.MUBResponseSchema],
    summary="List participants in the community",
)
async def list_participants(community: CommunityById) -> Sequence[Participant]:
    return await Participant.find_all_by_community_id(community_id=community.id)


@router.post(
    "/communities/{community_id}/participants/",
    status_code=status.HTTP_201_CREATED,
    response_model=Participant.MUBResponseSchema,
    summary="Create a new participant in the community",
)
async def create_participant(
    community: CommunityById, user_id: int, data: Participant.MUBPatchSchema
) -> Participant:
    return await Participant.create(
        community_id=community.id,
        user_id=user_id,
        **data.model_dump(exclude_defaults=True),
    )


@router.get(
    "/participants/{participant_id}/",
    response_model=Participant.MUBResponseSchema,
    summary="Retrieve any participant by id",
)
async def retrieve_participant(participant: ParticipantById) -> Participant:
    return participant


@router.patch(
    "/participants/{participant_id}/",
    response_model=Participant.MUBResponseSchema,
    summary="Update any participant by id",
)
async def patch_participant(
    participant: ParticipantById, data: Community.FullPatchSchema
) -> Participant:
    participant.update(**data.model_dump(exclude_defaults=True))
    return participant


@router.delete(
    "/participants/{participant_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any participant by id",
)
async def delete_participant(participant: ParticipantById) -> None:
    await participant.delete()
