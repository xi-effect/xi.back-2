from unittest.mock import Mock
from uuid import uuid4

import pytest


@pytest.fixture()
def notification_mock() -> Mock:
    notification_mock = Mock()
    notification_mock.id = uuid4()
    return notification_mock
