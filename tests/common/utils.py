from typing import Any

from pydantic import BaseModel

from tests.common.types import AnyJSON


def remove_none_values[K, V](source: dict[K, V | None]) -> dict[K, V]:
    return {key: value for key, value in source.items() if value is not None}


def repackage_json(schema: type[BaseModel], data: Any) -> AnyJSON:
    return schema.model_validate(data, from_attributes=True).model_dump(mode="json")
