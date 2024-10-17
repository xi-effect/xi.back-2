from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from httpx import Response
from pydantic import TypeAdapter

P = ParamSpec("P")
R = TypeVar("R")


def validate_json_response(
    type_adapter: TypeAdapter[R],
) -> Callable[[Callable[P, Awaitable[Response]]], Callable[P, Awaitable[R]]]:
    def validate_json_response_wrapper(
        function: Callable[P, Awaitable[Response]]
    ) -> Callable[P, Awaitable[R]]:
        async def validate_json_response_inner(*args: P.args, **kwargs: P.kwargs) -> R:
            response = await function(*args, **kwargs)
            response.raise_for_status()
            return type_adapter.validate_python(response.json())

        return validate_json_response_inner

    return validate_json_response_wrapper