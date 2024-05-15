from app.communities.models.categories_db import Category
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


class InvitationFullInputFactory(BaseModelFactory[Invitation.FullInputSchema]):
    __model__ = Invitation.FullInputSchema


class CategoryInputFactory(BaseModelFactory[Category.InputSchema]):
    __model__ = Category.InputSchema


class CategoryPatchFactory(BasePatchModelFactory[Category.PatchSchema]):
    __model__ = Category.PatchSchema
