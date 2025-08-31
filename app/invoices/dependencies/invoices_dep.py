from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.invoices.models.invoices_db import Invoice


class InvoiceResponses(Responses):
    INVOICE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Invoice not found"


@with_responses(InvoiceResponses)
async def get_invoice_by_id(invoice_id: Annotated[int, Path()]) -> Invoice:
    invoice = await Invoice.find_first_by_id(invoice_id)
    if invoice is None:
        raise InvoiceResponses.INVOICE_NOT_FOUND
    return invoice


InvoiceById = Annotated[Invoice, Depends(get_invoice_by_id)]
