import re
from random import randint
from time import time
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from freezegun import freeze_time

from app.notifications.utils import deep_links
from tests.common.mock_stack import MockStack
from tests.notifications.constants import ALLOWED_DEEP_LINK_PAYLOAD_PATTERN


@pytest.fixture()
def deep_link_provider() -> deep_links.DeepLinkProvider:
    return deep_links.DeepLinkProvider(
        secret_keys=[Fernet.generate_key().decode()],
        ttl=randint(60 * 5, 60 * 10),
    )


@pytest.fixture()
def user_id_for_deep_link() -> int:
    return randint(2**127, 2**128)


@pytest.fixture()
def deep_link_payload(
    deep_link_provider: deep_links.DeepLinkProvider,
    user_id_for_deep_link: int,
) -> str:
    return deep_link_provider.create_signed_link_payload(user_id=user_id_for_deep_link)


def test_payload_encoding_matches_regex(deep_link_payload: str) -> None:
    assert (
        re.fullmatch(ALLOWED_DEEP_LINK_PAYLOAD_PATTERN, deep_link_payload) is not None
    )


def test_payload_decoding(
    deep_link_provider: deep_links.DeepLinkProvider,
    user_id_for_deep_link: int,
    deep_link_payload: str,
) -> None:
    actual_decoded_user_id = deep_link_provider.verify_and_decode_signed_link_payload(
        link_payload=deep_link_payload
    )
    assert actual_decoded_user_id == user_id_for_deep_link


@freeze_time()
def test_payload_decoding_expired_deep_link(
    mock_stack: MockStack,
    deep_link_provider: deep_links.DeepLinkProvider,
    user_id_for_deep_link: int,
) -> None:
    deep_link_payload = deep_link_provider.create_signed_link_payload(
        user_id=user_id_for_deep_link
    )
    mock_stack.enter_mock(
        deep_links.DeepLinkProvider,
        "get_current_timestamp",
        return_value=time() + deep_link_provider.ttl + randint(60, 120),
    )

    with pytest.raises(deep_links.ExpiredDeepLinkException):
        deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=deep_link_payload
        )


def test_payload_decoding_invalid_deep_link_signature(
    deep_link_provider: deep_links.DeepLinkProvider,
    deep_link_payload: str,
) -> None:
    with pytest.raises(deep_links.InvalidDeepLinkSignatureException):
        deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=deep_link_payload[:-1]
        )


def test_payload_decoding_invalid_deep_link(
    deep_link_provider: deep_links.DeepLinkProvider,
) -> None:
    with pytest.raises(deep_links.InvalidDeepLinkException):
        deep_link_provider.verify_and_decode_signed_link_payload(
            link_payload=uuid4().hex
        )
