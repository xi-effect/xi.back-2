from enum import StrEnum, auto
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

from app.subscriptions.schemas.payments_sch import PaymentCorrelationSchema

# Reference for payment-related schemas:
# https://yookassa.ru/developers/api#create_payment

# Some fields are intentionally omitted, because they are not used


class YooKassaAmountSchema(BaseModel):
    value: str
    currency: Literal["RUB"] = "RUB"


class YooKassaReceiptItemSchema(BaseModel):
    description: str = Field(max_length=128)
    amount: YooKassaAmountSchema
    vat_code: Literal[1] = 1  # no VAT
    quantity: Literal[1] = 1
    measure: Literal["piece"] = "piece"
    payment_subject: Literal["service"] = "service"
    payment_mode: Literal["full_payment"] = "full_payment"


class YooKassaReceiptCustomerSchema(BaseModel):
    email: str


class YooKassaReceiptSchema(BaseModel):
    customer: YooKassaReceiptCustomerSchema
    items: list[YooKassaReceiptItemSchema]


class YooKassaRedirectConfirmationSchema(BaseModel):
    type: Literal["redirect"] = "redirect"
    return_url: str


class YooKassaCreatePaymentRequestSchema(BaseModel):
    amount: YooKassaAmountSchema
    capture: Literal[True] = True
    confirmation: YooKassaRedirectConfirmationSchema
    receipt: YooKassaReceiptSchema
    # metadata is the same for every payment for now, so the schema is not generic
    metadata: PaymentCorrelationSchema


# Reference for payment schemas:
# https://yookassa.ru/developers/api#payment_object


class YooKassaPaymentStatus(StrEnum):
    PENDING = auto()
    WAITING_FOR_CAPTURE = auto()
    SUCCEEDED = auto()
    CANCELED = auto()


class YooKassaBasePaymentSchema(BaseModel):
    id: str
    metadata: PaymentCorrelationSchema


class YooKassaConfirmationSchema(BaseModel):
    confirmation_url: str


class YooKassaPendingPaymentSchema(YooKassaBasePaymentSchema):
    status: Literal[YooKassaPaymentStatus.PENDING]
    confirmation: YooKassaConfirmationSchema


yookassa_pending_payment_type_adapter = TypeAdapter(YooKassaPendingPaymentSchema)


class YooKassaWaitingForCapturePaymentSchema(YooKassaBasePaymentSchema):
    status: Literal[YooKassaPaymentStatus.WAITING_FOR_CAPTURE]


class YooKassaSucceededPaymentSchema(YooKassaBasePaymentSchema):
    status: Literal[YooKassaPaymentStatus.SUCCEEDED]


class YooKassaCancellationDetailsSchema(BaseModel):
    reason: str


class YooKassaCanceledPaymentSchema(YooKassaBasePaymentSchema):
    status: Literal[YooKassaPaymentStatus.CANCELED]
    cancellation_details: YooKassaCancellationDetailsSchema


AnyYooKassaPaymentSchema = Annotated[
    YooKassaPendingPaymentSchema
    | YooKassaWaitingForCapturePaymentSchema
    | YooKassaSucceededPaymentSchema
    | YooKassaCanceledPaymentSchema,
    Field(discriminator="status"),
]

any_yookassa_payment_type_adapter: TypeAdapter[AnyYooKassaPaymentSchema] = TypeAdapter(
    AnyYooKassaPaymentSchema
)


# Reference for event schemas:
# https://yookassa.ru/developers/using-api/webhooks


class YooKassaEventType(StrEnum):
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_CANCELED = "payment.canceled"


class YooKassaEventObjectSchema(BaseModel):
    id: str = Field(pattern="^[A-Za-z0-9-]{1,50}$")


class YooKassaEventSchema(BaseModel):
    event: str
    object: YooKassaEventObjectSchema
