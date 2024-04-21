from app.communities.models.communities_db import Community
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class CommunityFullInputFactory(BaseModelFactory[Community.FullInputSchema]):
    __model__ = Community.FullInputSchema


class CommunityFullPatchFactory(BasePatchModelFactory[Community.FullPatchSchema]):
    __model__ = Community.FullPatchSchema
