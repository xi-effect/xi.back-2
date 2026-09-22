from typing import Any

from httpx import AsyncClient, BasicAuth

from app.common.bridges.utils import ResponsePipelineBuilder
from app.subscriptions.schemas.yookassa_sch import (
    YooKassaCreatePaymentRequestSchema,
    YooKassaPaymentResponseSchema,
    yookassa_payment_response_type_adapter,
)


class YooKassaClient(AsyncClient):
    def __init__(self, base_url: str, shop_id: str, secret_key: str) -> None:
        super().__init__(
            base_url=base_url,
            auth=BasicAuth(username=shop_id, password=secret_key),
        )

    async def create_payment(
        self,
        data: YooKassaCreatePaymentRequestSchema[Any],
        idempotence_key: str,
    ) -> YooKassaPaymentResponseSchema:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.post(
                    "/payments",
                    json=data.model_dump(mode="json"),
                    headers={"Idempotence-Key": idempotence_key},
                )
            )
            .validate_status_code()
            .validate_json(yookassa_payment_response_type_adapter)
        )
