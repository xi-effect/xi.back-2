from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt, Responses
from app.communities.dependencies.participants_dep import ParticipantById
from app.communities.dependencies.roles_dep import RoleById
from app.communities.models.participants_db import ParticipantRole

router = APIRouterExt(tags=["participant roles meta mub"])


class AssignRoleResponses(Responses):
    ROLE_ALREADY_ASSIGNED = 409, "Participant is already have this role"


@router.post(
    "/participants/{participant_id}/roles/{role_id}/",
    status_code=201,
    response_model=ParticipantRole.ResponseSchema,
    responses=AssignRoleResponses.responses(),
    summary="Assign a new role to a participant",
)
async def assign_role(participant: ParticipantById, role: RoleById) -> ParticipantRole:
    participant_role = await ParticipantRole.find_first_by_kwargs(
        participant_id=participant.id, role_id=role.id
    )
    if participant_role is not None:
        raise AssignRoleResponses.ROLE_ALREADY_ASSIGNED
    return await ParticipantRole.create(
        participant_id=participant.id,
        role_id=role.id,
    )


@router.get(
    "/participants/{participant_id}/roles/",
    response_model=list[ParticipantRole.ResponseSchema],
    summary="List roles of the participant",
)
async def list_participant_roles(
    participant: ParticipantById,
) -> Sequence[ParticipantRole]:
    return await ParticipantRole.find_all_by_kwargs(participant_id=participant.id)


class RemoveRoleResponses(Responses):
    ROLE_NOT_ASSIGNED = 409, "Participant does not have this role"


@router.delete(
    "/participants/{participant_id}/roles/{role_id}/",
    status_code=204,
    responses=RemoveRoleResponses.responses(),
    summary="Remove any participant's role by id",
)
async def remove_role(participant: ParticipantById, role: RoleById) -> None:
    participant_role = await ParticipantRole.find_first_by_kwargs(
        participant_id=participant.id, role_id=role.id
    )
    if participant_role is None:
        raise RemoveRoleResponses.ROLE_NOT_ASSIGNED
    await participant_role.delete()
