import pytest
from respx import MockRouter

from app.pochta.dependencies.unisender_go_dep import unisender_go_client_manager

pytestmark = pytest.mark.anyio


async def test_unisender_go_client_manager_client_calling_cached(
    unisender_go_mock: MockRouter,
) -> None:
    assert unisender_go_client_manager() is unisender_go_client_manager()


async def test_unisender_go_client_manager_calling_config_not_set() -> None:
    with pytest.raises(ValueError, match="Unisender GO api key is not set"):
        unisender_go_client_manager()
