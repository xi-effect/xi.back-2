from itsdangerous import BadSignature, URLSafeTimedSerializer
from pydantic import BaseModel, ValidationError


class SignedTokenProvider[T: BaseModel]:
    def __init__(
        self,
        secret_keys: list[str],
        encryption_ttl: int,
        payload_schema: type[T],
    ) -> None:
        self.serializer = URLSafeTimedSerializer(secret_key=secret_keys)
        self.encryption_ttl = encryption_ttl
        self.payload_schema = payload_schema

    def serialize_and_sign(self, payload: T) -> str:
        return self.serializer.dumps(payload.model_dump(mode="json"))

    def validate_and_deserialize(self, token: str) -> T | None:
        try:
            return self.payload_schema.model_validate(
                self.serializer.loads(token, max_age=self.encryption_ttl)
            )
        except (BadSignature, ValidationError):
            return None
