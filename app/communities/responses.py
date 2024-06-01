from app.common.fastapi_ext import Responses


class MoveResponses(Responses):
    INVALID_MOVE = 409, "Invalid move"


class LimitedListResponses(Responses):
    QUANTITY_EXCEEDED = 409, "Quantity exceeded"
