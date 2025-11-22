from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Literal, overload

import sentry_sdk
from httpx import Response
from pydantic import TypeAdapter


def set_extra_from_external_response(response: Response) -> None:
    sentry_sdk.set_extra("response", response)
    sentry_sdk.set_extra("response_headers", response.headers)
    sentry_sdk.set_extra("response_content", response.content[:1000])


@overload
def validate_external_json_response[**P, R](
    type_adapter: TypeAdapter[R],
) -> Callable[[Callable[P, Awaitable[Response]]], Callable[P, Awaitable[R]]]:
    pass


@overload
def validate_external_json_response[**P](
    type_adapter: Literal[None] = None,
) -> Callable[[Callable[P, Awaitable[Response]]], Callable[P, Awaitable[Response]]]:
    pass


def validate_external_json_response[**P](
    type_adapter: TypeAdapter[Any] | None = None,
) -> Callable[[Callable[P, Awaitable[Response]]], Callable[P, Awaitable[Any]]]:
    def validate_external_json_response_wrapper(
        function: Callable[P, Awaitable[Response]],
    ) -> Callable[P, Awaitable[Any]]:
        @wraps(function)
        async def validate_external_json_response_inner(
            *args: P.args, **kwargs: P.kwargs
        ) -> Any:
            with sentry_sdk.new_scope():
                response = await function(*args, **kwargs)
                set_extra_from_external_response(response=response)

                response.raise_for_status()
                if type_adapter is None:
                    return response
                return type_adapter.validate_python(response.json())

        return validate_external_json_response_inner

    return validate_external_json_response_wrapper
