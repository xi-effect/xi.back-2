from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt, Responses
from app.communities.dependencies.participants_dep import ParticipantById
from app.communities.dependencies.roles_dep import RoleById
from app.communities.models.participants_db import ParticipantRole

router = APIRouterExt(tags=["participant roles mub"])


class AssignRoleResponses(Responses):
    ROLE_ALREADY_ASSIGNED = 409, "Role already assigned to the participant"


@router.post(
    "/participants/{participant_id}/roles/{role_id}/",
    status_code=201,
    response_model=ParticipantRole.FullResponseSchema,
    responses=AssignRoleResponses.responses(),
    summary="Assign a role to a participant",
)
async def assign_role_to_participant(
    participant: ParticipantById, role: RoleById
) -> ParticipantRole:
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
    response_model=list[ParticipantRole.FullResponseSchema],
    summary="List roles of the participant",
)
async def list_participant_roles(
    participant: ParticipantById,
) -> Sequence[ParticipantRole]:
    return await ParticipantRole.find_all_by_kwargs(participant_id=participant.id)


class DepriveRoleResponses(Responses):
    ROLE_NOT_ASSIGNED = 404, "Participant does not have this role"


@router.delete(
    "/participants/{participant_id}/roles/{role_id}/",
    status_code=204,
    responses=DepriveRoleResponses.responses(),
    summary="Deprive any participant's role by id",
)
async def deprive_role(participant: ParticipantById, role: RoleById) -> None:
    participant_role = await ParticipantRole.find_first_by_kwargs(
        participant_id=participant.id, role_id=role.id
    )
    if participant_role is None:
        raise DepriveRoleResponses.ROLE_NOT_ASSIGNED
    await participant_role.delete()
