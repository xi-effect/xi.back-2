from typing import Any

from pydantic import BaseModel, ValidationError

from app.common.dependencies.authorization_dep import (
    ProxyAuthData,
    SessionIDHeader,
    UserIDHeader,
    UsernameHeader,
    construct_proxy_auth_data,
)
from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.invitations_dep import InvitationResponses
from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from app.communities.models.participants_db import Participant

router = APIRouterExt(tags=["community joining"])


class CommunityPreviewModel(BaseModel):
    community: Community.FullResponseSchema
    is_authorized: bool
    has_already_joined: bool


@router.get(
    "/invitations/by-code/{code}/community/",
    responses=InvitationResponses.responses(),
    response_model=CommunityPreviewModel,
    summary="Retrieve community preview by invitation code",
)
async def retrieve_community_by_invitation_code(
    code: str,
    session_id_token: SessionIDHeader = None,
    user_id_token: UserIDHeader = None,
    username_token: UsernameHeader = None,
) -> dict[str, Any]:
    proxy_auth_data: ProxyAuthData | None
    try:  # using try-except to use pydantic's validation
        proxy_auth_data = construct_proxy_auth_data(
            session_id_token=session_id_token,
            user_id_token=user_id_token,
            username_token=username_token,
        )
    except ValidationError:
        proxy_auth_data = None

    result = await Invitation.find_with_community_by_code(code)
    if result is None:
        raise InvitationResponses.INVITATION_NOT_FOUND
    community, invitation = result

    if not invitation.is_valid():
        # TODO delete invitation (errors do a rollback)
        raise InvitationResponses.INVITATION_NOT_FOUND

    if proxy_auth_data is None:
        participant = None
    else:
        participant = await Participant.find_first_by_kwargs(
            community_id=community.id, user_id=proxy_auth_data.user_id
        )

    return {
        "community": community,
        "is_authorized": proxy_auth_data is not None,
        "has_already_joined": participant is not None,
    }
