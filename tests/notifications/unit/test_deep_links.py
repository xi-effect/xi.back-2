import re
from random import randint
from time import time
from uuid import uuid4

import pytest
from freezegun import freeze_time

from app.notifications.config import telegram_deep_link_provider
from app.notifications.utils import deep_links
from tests.common.mock_stack import MockStack
from tests.notifications.constants import ALLOWED_DEEP_LINK_PAYLOAD_PATTERN


@pytest.fixture()
def user_id_for_deep_link() -> int:
    return randint(2**127, 2**128)


@pytest.fixture()
def deep_link_payload(user_id_for_deep_link: int) -> str:
    return telegram_deep_link_provider.create_signed_link_payload(
        user_id=user_id_for_deep_link
    )


def test_payload_encoding_matches_regex(deep_link_payload: str) -> None:
    assert (
        re.fullmatch(ALLOWED_DEEP_LINK_PAYLOAD_PATTERN, deep_link_payload) is not None
    )


def test_payload_decoding(
    user_id_for_deep_link: int,
    deep_link_payload: str,
) -> None:
    actual_decoded_user_id = (
        telegram_deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=deep_link_payload
        )
    )
    assert actual_decoded_user_id == user_id_for_deep_link


@freeze_time()
def test_payload_decoding_expired_deep_link(
    mock_stack: MockStack,
    deep_link_payload: str,
) -> None:
    mock_stack.enter_mock(
        telegram_deep_link_provider,
        "get_current_timestamp",
        return_value=time() + telegram_deep_link_provider.ttl + randint(2, 100),
    )
    with pytest.raises(deep_links.ExpiredDeepLinkException):
        telegram_deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=deep_link_payload
        )


def test_payload_decoding_invalid_deep_link_signature(
    deep_link_payload: str,
) -> None:
    with pytest.raises(deep_links.InvalidDeepLinkSignatureException):
        telegram_deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=deep_link_payload[:-1]
        )


def test_payload_decoding_invalid_deep_link() -> None:
    with pytest.raises(deep_links.InvalidDeepLinkException):
        telegram_deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=uuid4().hex
        )
