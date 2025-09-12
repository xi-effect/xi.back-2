from app.common.bridges.autocomplete_bdg import AutocompleteBridge
from app.common.bridges.communities_bdg import CommunitiesBridge
from app.common.bridges.messenger_bdg import MessengerBridge
from app.common.bridges.posts_bdg import PostsBridge
from app.common.bridges.storage_bdg import StorageBridge
from app.common.bridges.users_internal_bdg import UsersInternalBridge
from app.common.bridges.users_public_bdg import UsersPublicBridge

autocomplete_bridge = AutocompleteBridge()
communities_bridge = CommunitiesBridge()
messenger_bridge = MessengerBridge()
posts_bridge = PostsBridge()
users_internal_bridge = UsersInternalBridge()
users_public_bridge = UsersPublicBridge()
storage_bridge = StorageBridge()
