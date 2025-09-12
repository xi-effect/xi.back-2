import pytest
from starlette.testclient import TestClient

from app.autocomplete.models.subjects_db import Subject
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_subject_retrieving(
    internal_client: TestClient,
    subject: Subject,
    subject_data: AnyJSON,
) -> None:
    assert_response(
        internal_client.get(f"/internal/autocomplete-service/subjects/{subject.id}/"),
        expected_json=subject_data,
    )
