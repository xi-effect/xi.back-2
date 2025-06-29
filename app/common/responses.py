from starlette import status

from app.common.fastapi_ext import Responses


class LimitedListResponses(Responses):
    QUANTITY_EXCEEDED = status.HTTP_409_CONFLICT, "Quantity exceeded"
