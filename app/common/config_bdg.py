from app.common.bridges.autocomplete_bdg import AutocompleteBridge
from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.classrooms_bdg import ClassroomsBridge
from app.common.bridges.messenger_bdg import MessengerBridge
from app.common.bridges.notifications_bdg import NotificationsBridge
from app.common.bridges.pochta_bdg import PochtaBridge
from app.common.bridges.posts_bdg import PostsBridge
from app.common.bridges.storage_v2_bdg import StorageV2Bridge
from app.common.bridges.users_internal_bdg import UsersInternalBridge
from app.common.bridges.users_public_bdg import UsersPublicBridge

autocomplete_bridge = AutocompleteBridge()
classrooms_bridge = ClassroomsBridge()
messenger_bridge = MessengerBridge()
notifications_bridge = NotificationsBridge()
pochta_bridge = PochtaBridge()
posts_bridge = PostsBridge()
users_internal_bridge = UsersInternalBridge()
users_public_bridge = UsersPublicBridge()
storage_v2_bridge = StorageV2Bridge()

all_bridges: tuple[BaseBridge, ...] = (
    autocomplete_bridge,
    classrooms_bridge,
    messenger_bridge,
    notifications_bridge,
    pochta_bridge,
    posts_bridge,
    users_internal_bridge,
    users_public_bridge,
    storage_v2_bridge,
)
