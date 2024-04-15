from app.communities.models.communities_db import Community
from tests.common.polyfactory_ext import BaseModelFactory


class CommunityFullInputFactory(BaseModelFactory[Community.FullInputSchema]):
    __model__ = Community.FullInputSchema
