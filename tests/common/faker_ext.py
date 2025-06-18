import pytest
from faker import Faker
from faker.providers import internet
from faker_file.providers import (  # type: ignore[import-untyped]
    bin_file,
    pdf_file,
    webp_file,
)


@pytest.fixture(scope="session", autouse=True)
def _setup_faker(faker: Faker) -> None:
    faker.add_provider(internet)
    faker.add_provider(bin_file.BinFileProvider)
    faker.add_provider(webp_file.GraphicWebpFileProvider)
    faker.add_provider(pdf_file.PdfFileProvider)


@pytest.fixture(scope="session")
def faker(_session_faker: Faker) -> Faker:
    return _session_faker
