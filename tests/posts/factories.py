from app.posts.models.post_channels_db import PostChannel
from app.posts.models.posts_db import Post
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class PostChannelInputFactory(BaseModelFactory[PostChannel.InputSchema]):
    __model__ = PostChannel.InputSchema


class PostInputFactory(BaseModelFactory[Post.InputSchema]):
    __model__ = Post.InputSchema


class PostPatchFactory(BasePatchModelFactory[Post.PatchSchema]):
    __model__ = Post.PatchSchema
