from secrets import token_urlsafe


class TokenGenerator:
    def __init__(self, randomness: int, length: int) -> None:
        self.token_randomness = randomness
        self.token_length = length

    def generate_token(self) -> str:
        return token_urlsafe(self.token_randomness)[: self.token_length]
