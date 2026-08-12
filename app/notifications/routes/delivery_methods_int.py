from typing import Annotated

from fastapi import Path, Response
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    EmailDeliveryMethod,
)

router = APIRouterExt(tags=["delivery methods internal"])


@router.put(
    path=f"/users/{{user_id}}/delivery-methods/{DeliveryMethodKind.EMAIL}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Create or update an email delivery method for any user by id",
)
async def create_or_update_email_delivery_method(
    user_id: Annotated[int, Path()],
    data: EmailDeliveryMethod.InputSchema,
    response: Response,
) -> None:
    delivery_method = await EmailDeliveryMethod.find_first_by_user_id(user_id=user_id)
    if delivery_method is None:
        response.status_code = status.HTTP_201_CREATED
        await EmailDeliveryMethod.create(
            user_id=user_id,
            status=DeliveryMethodStatus.ACTIVE,
            **data.model_dump(),
        )
    else:
        delivery_method.update(**data.model_dump())
