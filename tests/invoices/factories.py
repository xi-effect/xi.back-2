from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import RecipientInvoice
from app.invoices.routes.invoices_tutor_rst import InvoiceFormSchema
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class InvoiceItemTemplateInputFactory(
    BaseModelFactory[InvoiceItemTemplate.InputSchema]
):
    __model__ = InvoiceItemTemplate.InputSchema


class InvoiceItemTemplatePatchFactory(
    BasePatchModelFactory[InvoiceItemTemplate.PatchSchema]
):
    __model__ = InvoiceItemTemplate.PatchSchema


class InvoiceInputFactory(BaseModelFactory[Invoice.InputSchema]):
    __model__ = Invoice.InputSchema


class InvoiceInputMUBFactory(BaseModelFactory[Invoice.InputMUBSchema]):
    __model__ = Invoice.InputMUBSchema


class InvoiceItemInputFactory(BaseModelFactory[InvoiceItem.InputSchema]):
    __model__ = InvoiceItem.InputSchema


class InvoiceFormFactory(BaseModelFactory[InvoiceFormSchema]):
    __model__ = InvoiceFormSchema


class InvoicePatchMUBFactory(BasePatchModelFactory[Invoice.PatchMUBSchema]):
    __model__ = Invoice.PatchMUBSchema


class RecipientInvoicePatchFactory(BasePatchModelFactory[RecipientInvoice.PatchSchema]):
    __model__ = RecipientInvoice.PatchSchema


class RecipientInvoicePaymentFactory(BaseModelFactory[RecipientInvoice.PaymentSchema]):
    __model__ = RecipientInvoice.PaymentSchema
