from starlette import status

from app.common.config_bdg import pochta_bridge
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.pochta_sch import EmailMessageInputSchema

router = APIRouterExt(tags=["email messages mub"])


@router.post(
    path="/email-messages/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Queue sending an email message",
)
async def queue_email_message_sending(data: EmailMessageInputSchema) -> None:
    await pochta_bridge.send_email_message(data)
