from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt, Responses
from app.communities.dependencies.participants_dep import ParticipantById
from app.communities.dependencies.roles_dep import RoleById
from app.communities.models.participants_db import ParticipantRole
from app.communities.models.roles_db import Role

router = APIRouterExt(tags=["participant roles mub"])


class AssignRoleResponses(Responses):
    ROLE_ALREADY_ASSIGNED = 409, "Role already assigned to the participant"


@router.post(
    "/participants/{participant_id}/roles/{role_id}/",
    status_code=204,
    responses=AssignRoleResponses.responses(),
    summary="Provide a role to a participant",
)
async def provide_role_to_participant(
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


@router.get(
    "/participants/{participant_id}/roles/",
    response_model=list[Role.ResponseSchema],
    summary="List roles of the participant",
)
async def list_participant_roles(
    participant: ParticipantById,
) -> Sequence[Role]:
    return participant.roles


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
