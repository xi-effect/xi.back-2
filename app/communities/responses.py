from starlette import status

from app.common.fastapi_ext import Responses


class MoveResponses(Responses):
    INVALID_MOVE = status.HTTP_409_CONFLICT, "Invalid move"


class LimitedListResponses(Responses):
    QUANTITY_EXCEEDED = status.HTTP_409_CONFLICT, "Quantity exceeded"
