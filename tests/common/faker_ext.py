import pytest
import rstr
from faker import Faker
from faker.providers import BaseProvider, internet


class RegexGeneratorProvider(BaseProvider):
    def generate_regex(self, pattern: str) -> str:
        return rstr.xeger(pattern)

    def username(self) -> str:
        return self.generate_regex("^[a-z0-9_.]{4,30}$")


@pytest.fixture(scope="session", autouse=True)
def _setup_faker(faker: Faker) -> None:
    faker.add_provider(internet)
    faker.add_provider(RegexGeneratorProvider)


@pytest.fixture(scope="session")
def faker(_session_faker: Faker) -> Faker:
    return _session_faker
