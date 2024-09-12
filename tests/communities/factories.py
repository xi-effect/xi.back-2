from datetime import timezone
from functools import partial
from typing import Annotated

from polyfactory import PostGenerated
from pydantic import AwareDatetime, PastDatetime, PositiveInt

from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from app.communities.models.participants_db import Participant
from app.communities.models.roles_db import Role
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class CommunityFullInputFactory(BaseModelFactory[Community.FullInputSchema]):
    __model__ = Community.FullInputSchema


class CommunityFullPatchFactory(BasePatchModelFactory[Community.FullPatchSchema]):
    __model__ = Community.FullPatchSchema


class ParticipantMUBPatchFactory(BasePatchModelFactory[Participant.MUBPatchSchema]):
    __model__ = Participant.MUBPatchSchema


class InvitationInputFactory(BaseModelFactory[Invitation.InputSchema]):
    __model__ = Invitation.InputSchema


class InvitationMUBInputFactory(BaseModelFactory[Invitation.MUBInputSchema]):
    __model__ = Invitation.MUBInputSchema


class ExpiredInvitationData(Invitation.MUBInputSchema):
    expiry: Annotated[PastDatetime, AwareDatetime]  # polyfactory doesn't support this


class ExpiredInvitationDataFactory(BaseModelFactory[ExpiredInvitationData]):
    __model__ = ExpiredInvitationData
    expiry = partial(BaseModelFactory.__faker__.past_datetime, tzinfo=timezone.utc)


class OverusedInvitationData(Invitation.MUBInputSchema):
    usage_limit: PositiveInt
    usage_count: int


class OverusedInvitationDataFactory(BaseModelFactory[OverusedInvitationData]):
    __model__ = OverusedInvitationData
    usage_count = PostGenerated(lambda _, values, *_a, **_k: values["usage_limit"])


class CategoryInputFactory(BaseModelFactory[Category.InputSchema]):
    __model__ = Category.InputSchema


class CategoryPatchFactory(BasePatchModelFactory[Category.PatchSchema]):
    __model__ = Category.PatchSchema


class ChannelInputFactory(BaseModelFactory[Channel.InputSchema]):
    __model__ = Channel.InputSchema


class ChannelPatchFactory(BasePatchModelFactory[Channel.PatchSchema]):
    __model__ = Channel.PatchSchema


class RoleInputFactory(BasePatchModelFactory[Role.InputSchema]):
    __model__ = Role.InputSchema


class RolePatchFactory(BasePatchModelFactory[Role.PatchSchema]):
    __model__ = Role.PatchSchema
