from app.common.bridges.communities_bdg import CommunitiesBridge
from app.common.bridges.messenger_bdg import MessengerBridge
from app.common.bridges.posts_bdg import PostsBridge
from app.common.bridges.public_users_bdg import PublicUsersBridge
from app.common.bridges.storage_bdg import StorageBridge

communities_bridge = CommunitiesBridge()
messenger_bridge = MessengerBridge()
posts_bridge = PostsBridge()
public_users_bridge = PublicUsersBridge()
storage_bridge = StorageBridge()
