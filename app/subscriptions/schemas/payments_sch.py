from uuid import UUID

from pydantic import BaseModel

from app.subscriptions.schemas.subscriptions_sch import SubscriptionPeriod


class PaymentCorrelationSchema(BaseModel):
    payment_id: UUID
    auto_renewal_period: SubscriptionPeriod | None = None
