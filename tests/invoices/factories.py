from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class InvoiceItemTemplateInputFactory(
    BaseModelFactory[InvoiceItemTemplate.InputSchema]
):
    __model__ = InvoiceItemTemplate.InputSchema


class InvoiceItemTemplatePatchFactory(
    BasePatchModelFactory[InvoiceItemTemplate.PatchSchema]
):
    __model__ = InvoiceItemTemplate.PatchSchema
