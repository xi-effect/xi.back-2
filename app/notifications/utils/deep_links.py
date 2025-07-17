from base64 import b32decode, b32encode
from time import time
from typing import ClassVar

from itsdangerous import Signer


class DeepLinkException(Exception):
    pass


class InvalidDeepLinkException(DeepLinkException):
    pass


class InvalidDeepLinkSignatureException(DeepLinkException):
    pass


class ExpiredDeepLinkException(DeepLinkException):
    pass


class TelegramDeepLinkProvider:
    sep: ClassVar[str] = "-"

    def __init__(self, secret_keys: list[str], ttl: int) -> None:
        self.signer = Signer(secret_keys)
        self.ttl = ttl

    def int_to_bytes(self, payload: int) -> bytes:
        return payload.to_bytes(length=(payload.bit_length() + 7) // 8)

    def bytes_to_int(self, payload: bytes) -> int:
        return int.from_bytes(payload)

    def urlsafe_b32encode_bytes(self, payload: bytes) -> str:
        return b32encode(payload).decode().rstrip("=")

    def urlsafe_b32decode_bytes(self, payload: str) -> bytes:
        last_block_width = len(payload) % 8
        if last_block_width != 0:
            payload += (8 - last_block_width) * "="
        return b32decode(payload.encode())

    def urlsafe_b32encode_int(self, payload: int) -> str:
        return self.urlsafe_b32encode_bytes(self.int_to_bytes(payload))

    def urlsafe_b32decode_int(self, payload: str) -> int:
        return self.bytes_to_int(self.urlsafe_b32decode_bytes(payload))

    def get_current_timestamp(self) -> int:
        return int(time())

    def create_link_payload(self, user_id: int) -> str:
        encoded_payload = self.urlsafe_b32encode_int(user_id)
        encoded_timestamp = self.urlsafe_b32encode_int(self.get_current_timestamp())
        return encoded_payload + self.sep + encoded_timestamp

    def create_signed_link_payload(self, user_id: int) -> str:
        link_payload = self.create_link_payload(user_id)
        signature = self.signer.get_signature(link_payload).decode()
        return link_payload + self.sep + signature

    def parse_link_payload(self, link_payload: str) -> tuple[str, str, str]:
        split_payload = link_payload.split(self.sep, maxsplit=2)
        if len(split_payload) < 2:
            raise InvalidDeepLinkException
        return split_payload[0], split_payload[1], split_payload[2]

    def verify_link_signature(
        self, encoded_payload: str, encoded_timestamp: str, signature: str
    ) -> None:
        if not self.signer.verify_signature(
            value=encoded_payload + self.sep + encoded_timestamp,
            sig=signature,
        ):
            raise InvalidDeepLinkSignatureException

    def verify_link_ttl(self, encoded_timestamp: str) -> None:
        timestamp = self.urlsafe_b32decode_int(encoded_timestamp)
        if timestamp + self.ttl < self.get_current_timestamp():
            raise ExpiredDeepLinkException

    def verify_and_decode_signed_link_payload(self, link_payload: str) -> int:
        encoded_payload, encoded_timestamp, signature = self.parse_link_payload(
            link_payload=link_payload
        )

        self.verify_link_signature(
            encoded_payload=encoded_payload,
            encoded_timestamp=encoded_timestamp,
            signature=signature,
        )

        self.verify_link_ttl(encoded_timestamp=encoded_timestamp)

        return self.urlsafe_b32decode_int(encoded_payload)
