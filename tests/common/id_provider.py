import random

import pytest


class IDProvider:
    def __init__(self) -> None:
        self._count: int = random.randint(
            0, 10000
        )  # noqa: S311  # no cryptography involved

    def generate_id(self) -> int:
        self._count += 1
        return self._count


@pytest.fixture(scope="session")
def id_provider() -> IDProvider:
    return IDProvider()
