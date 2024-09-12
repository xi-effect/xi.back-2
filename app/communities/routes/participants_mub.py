from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt, Responses
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.dependencies.participants_dep import ParticipantById
from app.communities.dependencies.roles_dep import RoleById
from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant, ParticipantRole

router = APIRouterExt(tags=["participants meta mub"])


@router.get(
    "/communities/{community_id}/participants/",
    response_model=list[Participant.MUBItemSchema],
    summary="List participants in the community",
)
async def list_participants(community: CommunityById) -> Sequence[Participant]:
    return await Participant.find_all_by_kwargs(
        Participant.created_at, community_id=community.id
    )


@router.post(
    "/communities/{community_id}/participants/",
    status_code=201,
    response_model=Participant.MUBItemSchema,
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
    status_code=204,
    summary="Delete any participant by id",
)
async def delete_participant(participant: ParticipantById) -> None:
    await participant.delete()


class AssignRoleResponses(Responses):
    ROLE_ALREADY_ASSIGNED = 409, "Role already assigned to the participant"


@router.post(
    "/participants/{participant_id}/roles/{role_id}/",
    status_code=204,
    responses=AssignRoleResponses.responses(),
    summary="Assign a role to a participant",
)
async def assign_role_to_participant(
    participant: ParticipantById, role: RoleById
) -> None:
    participant_role = await ParticipantRole.find_first_by_kwargs(
        participant_id=participant.id, role_id=role.id
    )
    if participant_role is not None:
        raise AssignRoleResponses.ROLE_ALREADY_ASSIGNED
    await ParticipantRole.create(
        participant_id=participant.id,
        role_id=role.id,
    )


class DeassignRoleResponses(Responses):
    ROLE_NOT_ASSIGNED = 404, "Role is not assigned to the participant"


@router.delete(
    "/participants/{participant_id}/roles/{role_id}/",
    status_code=204,
    responses=DeassignRoleResponses.responses(),
    summary="Deassign any participant's role by id",
)
async def deassign_role_from_participant(
    participant: ParticipantById, role: RoleById
) -> None:
    participant_role = await ParticipantRole.find_first_by_kwargs(
        participant_id=participant.id, role_id=role.id
    )
    if participant_role is None:
        raise DeassignRoleResponses.ROLE_NOT_ASSIGNED
    await participant_role.delete()
