from httpx import AsyncClient, BasicAuth

from app.common.bridges.utils import ResponsePipelineBuilder
from app.subscriptions.schemas.yookassa_sch import (
    AnyYooKassaPaymentSchema,
    YooKassaCreatePaymentRequestSchema,
    YooKassaPendingPaymentSchema,
    any_yookassa_payment_type_adapter,
    yookassa_pending_payment_type_adapter,
)


class YooKassaClient(AsyncClient):
    def __init__(self, base_url: str, shop_id: str, secret_key: str) -> None:
        super().__init__(
            base_url=base_url,
            auth=BasicAuth(username=shop_id, password=secret_key),
        )

    async def create_payment(
        self,
        data: YooKassaCreatePaymentRequestSchema,
        idempotence_key: str,
    ) -> YooKassaPendingPaymentSchema:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.post(
                    "/payments",
                    json=data.model_dump(mode="json"),
                    headers={"Idempotence-Key": idempotence_key},
                )
            )
            .validate_status_code()
            .validate_json(yookassa_pending_payment_type_adapter)
        )

    async def retrieve_payment(
        self, provider_payment_id: str
    ) -> AnyYooKassaPaymentSchema:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.get(f"/payments/{provider_payment_id}")
            )
            .validate_status_code()
            .validate_json(any_yookassa_payment_type_adapter)
        )
