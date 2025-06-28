import pytest
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.factories import ProxyAuthDataFactory
from tests.invoices import factories


@pytest.fixture()
def creator_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def creator_user_id(creator_auth_data: ProxyAuthData) -> int:
    return creator_auth_data.user_id


@pytest.fixture()
def creator_client(client: TestClient, creator_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=creator_auth_data.as_headers)


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
    creator_user_id: int,
) -> InvoiceItemTemplate:
    async with active_session():
        return await InvoiceItemTemplate.create(
            **factories.InvoiceItemTemplateInputFactory.build_python(),
            creator_user_id=creator_user_id,
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
