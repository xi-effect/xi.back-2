from base64 import urlsafe_b64encode
from collections.abc import Callable
from secrets import token_bytes

from cryptography.fernet import Fernet, InvalidToken, MultiFernet


class CryptographyProvider:
    def __init__(self, fernet_key_list: list[str], encryption_ttl: int) -> None:
        self.encryptor = MultiFernet((Fernet(key.encode()) for key in fernet_key_list))
        self.encryption_ttl: int = encryption_ttl

    def encrypt(self, data: str) -> str:
        return self.encryptor.encrypt(msg=data.encode()).decode()

    def decrypt(self, encrypted_data: bytes | str) -> str | None:
        try:
            return self.encryptor.decrypt(
                encrypted_data, ttl=self.encryption_ttl
            ).decode()
        except InvalidToken:
            return None


class TokenGenerator:
    def __init__(
        self,
        randomness: int,
        length: int,
        encoder: Callable[[bytes], bytes] | None = None,
    ) -> None:
        self.token_randomness = randomness
        self.token_length = length
        self.encoder: Callable[[bytes], bytes] = encoder or urlsafe_b64encode

    def generate_token(self) -> str:
        return (
            self.encoder(token_bytes(self.token_randomness))
            .rstrip(b"=")
            .decode("ascii")[: self.token_length]
        )
