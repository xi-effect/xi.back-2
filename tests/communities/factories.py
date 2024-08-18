from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from app.communities.models.invitations_db import Invitation
from app.communities.models.participants_db import Participant
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


class CategoryInputFactory(BaseModelFactory[Category.InputSchema]):
    __model__ = Category.InputSchema


class CategoryPatchFactory(BasePatchModelFactory[Category.PatchSchema]):
    __model__ = Category.PatchSchema


class ChannelInputFactory(BaseModelFactory[Channel.InputSchema]):
    __model__ = Channel.InputSchema


class ChannelPatchFactory(BasePatchModelFactory[Channel.PatchSchema]):
    __model__ = Channel.PatchSchema
