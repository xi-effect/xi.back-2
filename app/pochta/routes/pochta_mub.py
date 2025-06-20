from email.message import EmailMessage
from typing import Annotated

from fastapi import File, Form, HTTPException, UploadFile
from starlette import status

from app.common.config import settings, smtp_client
from app.common.fastapi_ext import APIRouterExt

router = APIRouterExt(tags=["pochta mub"])


@router.post(
    "/emails-from-file/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Send email from uploaded file",
)
async def send_email_from_file(
    receiver: Annotated[str, Form()],
    subject: Annotated[str, Form()],
    file: Annotated[UploadFile, File(description="text/html")],
) -> None:
    if smtp_client is None or settings.email is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Email config is not set"
        )

    message = EmailMessage()
    message["To"] = receiver
    message["Subject"] = subject
    message["From"] = settings.email.username
    message.set_content((await file.read()).decode(), subtype="html")

    async with smtp_client as smtp:
        await smtp.send_message(message)
