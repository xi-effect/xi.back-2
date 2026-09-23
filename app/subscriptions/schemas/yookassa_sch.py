from typing import Literal

from pydantic import BaseModel, Field, TypeAdapter

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


class YooKassaCreatePaymentRequestSchema[MetadataSchema: BaseModel](BaseModel):
    amount: YooKassaAmountSchema
    capture: Literal[True] = True
    confirmation: YooKassaRedirectConfirmationSchema
    receipt: YooKassaReceiptSchema
    metadata: MetadataSchema


class YooKassaConfirmationResponseSchema(BaseModel):
    confirmation_url: str


class YooKassaPaymentResponseSchema(BaseModel):
    id: str
    confirmation: YooKassaConfirmationResponseSchema


yookassa_payment_response_type_adapter = TypeAdapter(YooKassaPaymentResponseSchema)
