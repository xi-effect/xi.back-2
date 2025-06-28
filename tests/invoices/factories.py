from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice
from app.invoices.routes.invoices_rst import InvoiceFormSchema
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


class InvoiceItemInputFactory(BaseModelFactory[InvoiceItem.InputSchema]):
    __model__ = InvoiceItem.InputSchema


class InvoiceFormFactory(BaseModelFactory[InvoiceFormSchema]):
    __model__ = InvoiceFormSchema
