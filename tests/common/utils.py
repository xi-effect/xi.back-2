def remove_none_values[K, V](source: dict[K, V | None]) -> dict[K, V]:
    return {key: value for key, value in source.items() if value is not None}
