from secrets import token_urlsafe

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
    def __init__(self, randomness: int, length: int) -> None:
        self.token_randomness = randomness
        self.token_length = length

    def generate_token(self) -> str:
        return token_urlsafe(self.token_randomness)[: self.token_length]
