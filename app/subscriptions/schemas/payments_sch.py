from uuid import UUID

from pydantic import BaseModel


class PaymentCorrelationSchema(BaseModel):
    payment_id: UUID
