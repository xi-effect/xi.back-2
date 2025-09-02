from decimal import Decimal

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate
from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.factories import ProxyAuthDataFactory
from tests.invoices import factories


@pytest.fixture()
def tutor_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def tutor_id(tutor_auth_data: ProxyAuthData) -> int:
    return tutor_auth_data.user_id


@pytest.fixture()
def tutor_client(client: TestClient, tutor_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=tutor_auth_data.as_headers)


@pytest.fixture()
def student_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def student_id(student_auth_data: ProxyAuthData) -> int:
    return student_auth_data.user_id


@pytest.fixture()
def student_client(
    client: TestClient,
    student_auth_data: ProxyAuthData,
) -> TestClient:
    return TestClient(client.app, headers=student_auth_data.as_headers)


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_client(
    client: TestClient,
    outsider_auth_data: ProxyAuthData,
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)


@pytest.fixture()
async def invoice_item_template(
    active_session: ActiveSession,
    tutor_id: int,
) -> InvoiceItemTemplate:
    async with active_session():
        return await InvoiceItemTemplate.create(
            **factories.InvoiceItemTemplateInputFactory.build_python(),
            tutor_id=tutor_id,
        )


@pytest.fixture()
async def invoice_item_template_data(
    invoice_item_template: InvoiceItemTemplate,
) -> AnyJSON:
    return InvoiceItemTemplate.ResponseSchema.model_validate(
        invoice_item_template
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_invoice_item_template_id(
    active_session: ActiveSession,
    invoice_item_template: InvoiceItemTemplate,
) -> int:
    async with active_session():
        await invoice_item_template.delete()
    return invoice_item_template.id


@pytest.fixture()
async def invoice_data(invoice: Invoice) -> AnyJSON:
    return Invoice.ResponseSchema.model_validate(
        invoice, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_invoice_id(active_session: ActiveSession, invoice: Invoice) -> int:
    async with active_session():
        await invoice.delete()
    return invoice.id


@pytest.fixture()
def total(faker: Faker) -> Decimal:
    return faker.pydecimal(right_digits=2, positive=True)


@pytest.fixture()
async def invoice(active_session: ActiveSession, tutor_id: int) -> Invoice:
    async with active_session():
        return await Invoice.create(
            **factories.InvoiceInputFactory.build_python(), tutor_id=tutor_id
        )


@pytest.fixture()
async def recipient_invoice(
    active_session: ActiveSession, student_id: int, total: Decimal, invoice: Invoice
) -> RecipientInvoice:
    async with active_session():
        return await RecipientInvoice.create(
            invoice=invoice,
            student_id=student_id,
            total=total,
            status=PaymentStatus.WF_PAYMENT,
        )


@pytest.fixture()
def recipient_invoice_data(recipient_invoice: RecipientInvoice) -> AnyJSON:
    return RecipientInvoice.TutorResponseSchema.model_validate(
        recipient_invoice
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_recipient_invoice_id(
    active_session: ActiveSession, recipient_invoice: RecipientInvoice
) -> int:
    async with active_session():
        await recipient_invoice.delete()
    return recipient_invoice.id
