from typing import Annotated

from fastapi import Depends
from httpx import AsyncClient, Response
from pydantic import TypeAdapter

from app.common.bridges.utils import validate_json_response
from app.common.config import settings
from app.pochta.schemas.unisender_go_sch import (
    UnisenderGoSendEmailRequestSchema,
    UnisenderGoSendEmailSuccessfulResponseSchema,
)


class UnisenderGoClient:
    def __init__(self, api_key: str) -> None:
        self.client: AsyncClient = AsyncClient(
            base_url="https://go2.unisender.ru/ru/transactional",
            headers={"X-API-KEY": api_key},
        )

    @validate_json_response(TypeAdapter(UnisenderGoSendEmailSuccessfulResponseSchema))
    async def send_email(
        self,
        data: UnisenderGoSendEmailRequestSchema,
    ) -> Response:
        # TODO better error handling
        return await self.client.post(
            url="/api/v1/email/send.json",
            json=data.model_dump(mode="json", exclude_none=True),
        )


class UnisenderGoClientManager:
    def __init__(self) -> None:
        self.unisender_go_client: UnisenderGoClient | None = None
        self.unisender_go_api_key = settings.unisender_go_api_key

    def __call__(self) -> UnisenderGoClient:
        if self.unisender_go_client is not None:
            return self.unisender_go_client
        if self.unisender_go_api_key is None:
            raise ValueError("Unisender GO api key is not set")
        self.unisender_go_client = UnisenderGoClient(api_key=self.unisender_go_api_key)
        return self.unisender_go_client


unisender_go_client_manager = UnisenderGoClientManager()

UnisenderGoClientDep = Annotated[
    UnisenderGoClient, Depends(unisender_go_client_manager)
]
