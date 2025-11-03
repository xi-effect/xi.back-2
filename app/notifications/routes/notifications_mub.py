from starlette import status

from app.common.config_bdg import notifications_bridge
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.notifications_sch import NotificationInputSchema

router = APIRouterExt(tags=["notifications mub"])


@router.post(
    path="/notifications/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Queue sending a new notification to multiple users by ids",
)
async def queue_notification_sending(data: NotificationInputSchema) -> None:
    await notifications_bridge.send_notification(data)
