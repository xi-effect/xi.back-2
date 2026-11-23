import random
from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

import pytest
from faker import Faker
from pydantic import BaseModel
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import (
    PaymentStatus,
    PaymentType,
    RecipientInvoice,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.id_provider import IDProvider
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values, repackage_json
from tests.invoices import factories

pytestmark = pytest.mark.anyio

PAYMENT_STATUSES = list(PaymentStatus)
PAYMENT_TYPES = [*PaymentType, None]
USER_COUNT = 2
CLASSROOM_COUNT = 2
RECIPIENT_INVOICES_PER_USER = len(PAYMENT_STATUSES) * len(PAYMENT_TYPES)
RECIPIENT_INVOICES_LIST_SIZE = RECIPIENT_INVOICES_PER_USER * USER_COUNT
CLASSROOM_RECIPIENT_INVOICES_LIST_SIZE = RECIPIENT_INVOICES_LIST_SIZE // CLASSROOM_COUNT


@pytest.fixture()
def classroom_ids(id_provider: IDProvider) -> Sequence[int]:
    return [id_provider.generate_id() for _ in range(CLASSROOM_COUNT)]


@pytest.fixture()
def student_ids(id_provider: IDProvider) -> Sequence[int]:
    return [id_provider.generate_id() for _ in range(USER_COUNT)]


@pytest.fixture()
def tutor_ids(id_provider: IDProvider) -> Sequence[int]:
    return [id_provider.generate_id() for _ in range(USER_COUNT)]


async def create_recipient_invoice(
    index: int,
    tutor_id: int,
    student_id: int,
    classroom_id: int,
    created_at: datetime,
) -> RecipientInvoice:
    invoice: Invoice = await Invoice.create(
        **factories.InvoiceInputFactory.build_python(),
        tutor_id=tutor_id,
        classroom_id=classroom_id,
        created_at=created_at,
    )
    return await RecipientInvoice.create(
        invoice=invoice,
        student_id=student_id,
        total=Decimal(index + 1),
        status=PAYMENT_STATUSES[index % len(PAYMENT_STATUSES)],
        payment_type=PAYMENT_TYPES[index // len(PAYMENT_STATUSES) % len(PAYMENT_TYPES)],
    )


@pytest.fixture()
async def tutor_recipient_invoices(
    faker: Faker,
    active_session: ActiveSession,
    tutor_id: int,
    classroom_ids: Sequence[int],
    student_ids: Sequence[int],
) -> AsyncIterator[list[RecipientInvoice]]:
    last_created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    recipient_invoices: list[RecipientInvoice] = []

    async with active_session():
        for i in range(RECIPIENT_INVOICES_LIST_SIZE):
            last_created_at -= timedelta(minutes=faker.random_int(min=1))
            recipient_invoices.append(
                await create_recipient_invoice(
                    index=i,
                    tutor_id=tutor_id,
                    student_id=student_ids[i // RECIPIENT_INVOICES_PER_USER],
                    classroom_id=classroom_ids[i % CLASSROOM_COUNT],
                    created_at=last_created_at,
                )
            )

    recipient_invoices.sort(
        key=lambda recipient_invoice: recipient_invoice.created_at, reverse=True
    )

    yield recipient_invoices

    async with active_session():
        for recipient_invoice in recipient_invoices:
            await recipient_invoice.invoice.delete()


@pytest.fixture()
async def student_recipient_invoices(
    faker: Faker,
    active_session: ActiveSession,
    student_id: int,
    classroom_ids: Sequence[int],
    tutor_ids: Sequence[int],
) -> AsyncIterator[list[RecipientInvoice]]:
    last_created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    recipient_invoices: list[RecipientInvoice] = []

    async with active_session():
        for i in range(RECIPIENT_INVOICES_LIST_SIZE):
            last_created_at -= timedelta(minutes=faker.random_int(min=1))
            recipient_invoices.append(
                await create_recipient_invoice(
                    index=i,
                    tutor_id=tutor_ids[i // RECIPIENT_INVOICES_PER_USER],
                    student_id=student_id,
                    classroom_id=classroom_ids[i % CLASSROOM_COUNT],
                    created_at=last_created_at,
                )
            )

    recipient_invoices.sort(
        key=lambda recipient_invoice: recipient_invoice.created_at, reverse=True
    )

    yield recipient_invoices

    async with active_session():
        for recipient_invoice in recipient_invoices:
            await recipient_invoice.invoice.delete()


def convert_recipient_invoices(
    recipient_invoices: Sequence[RecipientInvoice],
    response_schema: type[BaseModel],
) -> Iterator[AnyJSON]:
    yield from (
        repackage_json(response_schema, recipient_invoice)
        for recipient_invoice in recipient_invoices
    )


recipient_invoice_list_role_parametrization = pytest.mark.parametrize(
    ("role", "authorized_client", "recipient_invoices", "response_schema"),
    [
        pytest.param(
            "tutor",
            lf("tutor_client"),
            lf("tutor_recipient_invoices"),
            RecipientInvoice.TutorResponseSchema,
            id="tutor",
        ),
        pytest.param(
            "student",
            lf("student_client"),
            lf("student_recipient_invoices"),
            RecipientInvoice.StudentResponseSchema,
            id="student",
        ),
    ],
)

empty_filters_parametrization = pytest.mark.parametrize(
    "filters",
    [
        pytest.param(None, id="omitted_filters"),
        pytest.param({}, id="empty_filters"),
    ],
)


@recipient_invoice_list_role_parametrization
@empty_filters_parametrization
@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, RECIPIENT_INVOICES_LIST_SIZE, id="start_to_end"),
        pytest.param(0, RECIPIENT_INVOICES_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            RECIPIENT_INVOICES_LIST_SIZE // 2,
            RECIPIENT_INVOICES_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_recipient_invoices_listing(
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    filters: AnyJSON | None,
    offset: int,
    limit: int,
) -> None:
    cursor = None if offset == 0 else recipient_invoices[offset - 1]

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}/recipient-invoices/searches/",
            json=remove_none_values(
                {
                    "cursor": (
                        None
                        if cursor is None
                        else {
                            "created_at": cursor.created_at.isoformat(),
                            "recipient_invoice_id": cursor.id,
                        }
                    ),
                    "limit": limit,
                    "filters": filters,
                }
            ),
        ),
        expected_json=list(
            convert_recipient_invoices(
                recipient_invoices[offset : offset + limit],
                response_schema,
            )
        ),
    )


@pytest.fixture()
def random_classroom_id(classroom_ids: Sequence[int]) -> int:
    return random.choice(classroom_ids)


@recipient_invoice_list_role_parametrization
@empty_filters_parametrization
@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, CLASSROOM_RECIPIENT_INVOICES_LIST_SIZE, id="start_to_end"),
        pytest.param(
            0,
            CLASSROOM_RECIPIENT_INVOICES_LIST_SIZE // 2,
            id="start_to_middle",
        ),
        pytest.param(
            CLASSROOM_RECIPIENT_INVOICES_LIST_SIZE // 2,
            CLASSROOM_RECIPIENT_INVOICES_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_classroom_recipient_invoices_listing(
    random_classroom_id: int,
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    filters: AnyJSON | None,
    offset: int,
    limit: int,
) -> None:
    candidate_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if recipient_invoice.classroom_id == random_classroom_id
    ]
    cursor = None if offset == 0 else candidate_recipient_invoices[offset - 1]

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}"
            f"/classrooms/{random_classroom_id}/recipient-invoices/searches/",
            json=remove_none_values(
                {
                    "cursor": (
                        None
                        if cursor is None
                        else {
                            "created_at": cursor.created_at.isoformat(),
                            "recipient_invoice_id": cursor.id,
                        }
                    ),
                    "limit": limit,
                    "filters": filters,
                }
            ),
        ),
        expected_json=list(
            convert_recipient_invoices(
                candidate_recipient_invoices[offset : offset + limit],
                response_schema,
            )
        ),
    )


recipient_invoice_list_classroom_parametrization = pytest.mark.parametrize(
    "classroom_id",
    [
        pytest.param(None, id="all_classrooms"),
        pytest.param(lf("random_classroom_id"), id="one_classroom"),
    ],
)


@recipient_invoice_list_role_parametrization
@recipient_invoice_list_classroom_parametrization
@pytest.mark.parametrize(
    "statuses",
    [
        *[
            pytest.param({payment_status}, id=payment_status)
            for payment_status in PAYMENT_STATUSES
        ],
        pytest.param(set(PAYMENT_STATUSES), id="all_statuses"),
    ],
)
async def test_recipient_invoices_listing_filtered_by_statuses(
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_id: int | None,
    statuses: set[PaymentStatus],
) -> None:
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}"
            f"{prefix}/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": {"status__in": list(statuses)},
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in recipient_invoices
                    if recipient_invoice.status in statuses
                    and (
                        classroom_id is None
                        or recipient_invoice.classroom_id == classroom_id
                    )
                ],
                response_schema,
            )
        ),
    )


@recipient_invoice_list_role_parametrization
@recipient_invoice_list_classroom_parametrization
@pytest.mark.parametrize(
    "payment_types",
    [
        *[
            pytest.param({payment_type}, id=str(payment_type))
            for payment_type in PAYMENT_TYPES
        ],
        pytest.param(set(PAYMENT_TYPES), id="all_payment_types"),
    ],
)
async def test_recipient_invoices_listing_filtered_by_payment_types(
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_id: int | None,
    payment_types: set[PaymentType | None],
) -> None:
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}"
            f"{prefix}/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": {"payment_type__in": list(payment_types)},
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in recipient_invoices
                    if recipient_invoice.payment_type in payment_types
                    and (
                        classroom_id is None
                        or recipient_invoice.classroom_id == classroom_id
                    )
                ],
                response_schema,
            )
        ),
    )


@pytest.mark.parametrize(
    "student_indexes",
    [
        pytest.param([0], id="single_student"),
        pytest.param([0, 1], id="multiple_students"),
    ],
)
async def test_tutor_recipient_invoices_listing_filtered_by_student_ids(
    tutor_client: TestClient,
    student_ids: Sequence[int],
    tutor_recipient_invoices: list[RecipientInvoice],
    student_indexes: list[int],
) -> None:
    student_id__in = {student_ids[student_index] for student_index in student_indexes}

    assert_response(
        tutor_client.post(
            "/api/protected/invoice-service/roles/tutor/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": {"student_id__in": list(student_id__in)},
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in tutor_recipient_invoices
                    if recipient_invoice.student_id in student_id__in
                ],
                RecipientInvoice.TutorResponseSchema,
            )
        ),
    )


@pytest.mark.parametrize(
    "tutor_indexes",
    [
        pytest.param([0], id="single_tutor"),
        pytest.param([0, 1], id="multiple_tutors"),
    ],
)
async def test_student_recipient_invoices_listing_filtered_by_tutor_ids(
    student_client: TestClient,
    tutor_ids: Sequence[int],
    student_recipient_invoices: list[RecipientInvoice],
    tutor_indexes: list[int],
) -> None:
    tutor_id__in = {tutor_ids[tutor_index] for tutor_index in tutor_indexes}

    assert_response(
        student_client.post(
            "/api/protected/invoice-service/roles/student/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": {"tutor_id__in": list(tutor_id__in)},
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in student_recipient_invoices
                    if recipient_invoice.tutor_id in tutor_id__in
                ],
                RecipientInvoice.StudentResponseSchema,
            )
        ),
    )


@recipient_invoice_list_role_parametrization
@recipient_invoice_list_classroom_parametrization
@pytest.mark.parametrize(
    ("is_lower_bound_specified", "is_upper_bound_specified"),
    [
        pytest.param(True, False, id="lower_bound_only"),
        pytest.param(False, True, id="upper_bound_only"),
        pytest.param(True, True, id="both_bounds"),
    ],
)
async def test_recipient_invoices_listing_filtered_by_created_at(
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_id: int | None,
    is_lower_bound_specified: bool,
    is_upper_bound_specified: bool,
) -> None:
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"
    candidate_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if classroom_id is None or recipient_invoice.classroom_id == classroom_id
    ]
    lower_recipient_invoice, upper_recipient_invoice = sorted(
        random.sample(candidate_recipient_invoices, 2),
        key=lambda recipient_invoice: recipient_invoice.created_at,
    )

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}"
            f"{prefix}/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": remove_none_values(
                    {
                        "created_at__ge": (
                            lower_recipient_invoice.created_at.isoformat()
                            if is_lower_bound_specified
                            else None
                        ),
                        "created_at__lt": (
                            upper_recipient_invoice.created_at.isoformat()
                            if is_upper_bound_specified
                            else None
                        ),
                    }
                ),
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in candidate_recipient_invoices
                    if (
                        not is_lower_bound_specified
                        or recipient_invoice.created_at
                        >= lower_recipient_invoice.created_at
                    )
                    and (
                        not is_upper_bound_specified
                        or recipient_invoice.created_at
                        < upper_recipient_invoice.created_at
                    )
                ],
                response_schema,
            )
        ),
    )


@recipient_invoice_list_role_parametrization
@recipient_invoice_list_classroom_parametrization
@pytest.mark.parametrize(
    ("is_lower_bound_specified", "is_upper_bound_specified"),
    [
        pytest.param(True, False, id="lower_bound_only"),
        pytest.param(False, True, id="upper_bound_only"),
        pytest.param(True, True, id="both_bounds"),
    ],
)
async def test_recipient_invoices_listing_filtered_by_total(
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_id: int | None,
    is_lower_bound_specified: bool,
    is_upper_bound_specified: bool,
) -> None:
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"
    candidate_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if classroom_id is None or recipient_invoice.classroom_id == classroom_id
    ]
    lower_recipient_invoice, upper_recipient_invoice = sorted(
        random.sample(candidate_recipient_invoices, 2),
        key=lambda recipient_invoice: recipient_invoice.total,
    )

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}"
            f"{prefix}/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": remove_none_values(
                    {
                        "total__ge": (
                            str(lower_recipient_invoice.total)
                            if is_lower_bound_specified
                            else None
                        ),
                        "total__le": (
                            str(upper_recipient_invoice.total)
                            if is_upper_bound_specified
                            else None
                        ),
                    }
                ),
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in candidate_recipient_invoices
                    if (
                        not is_lower_bound_specified
                        or recipient_invoice.total >= lower_recipient_invoice.total
                    )
                    and (
                        not is_upper_bound_specified
                        or recipient_invoice.total <= upper_recipient_invoice.total
                    )
                ],
                response_schema,
            )
        ),
    )


@recipient_invoice_list_role_parametrization
@recipient_invoice_list_classroom_parametrization
async def test_recipient_invoices_listing_filtered_by_equal_total_bounds(
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_id: int | None,
) -> None:
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"
    candidate_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if classroom_id is None or recipient_invoice.classroom_id == classroom_id
    ]
    total = random.choice(candidate_recipient_invoices).total

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}"
            f"{prefix}/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": {"total__ge": str(total), "total__le": str(total)},
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in candidate_recipient_invoices
                    if recipient_invoice.total == total
                ],
                response_schema,
            )
        ),
    )


recipient_invoice_role_parametrization = pytest.mark.parametrize(
    ("role", "authorized_client"),
    [
        pytest.param("tutor", lf("tutor_client"), id="tutor"),
        pytest.param("student", lf("student_client"), id="student"),
    ],
)


@recipient_invoice_role_parametrization
async def test_recipient_invoices_listing_invalid_created_at_range(
    faker: Faker,
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
) -> None:
    created_at__lt = faker.date_time_between(tzinfo=timezone.utc)

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}/recipient-invoices/searches/",
            json={
                "filters": {
                    "created_at__ge": faker.date_time_between(
                        start_date=created_at__lt, tzinfo=timezone.utc
                    ).isoformat(),
                    "created_at__lt": created_at__lt.isoformat(),
                }
            },
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body", "filters"],
                    "msg": "Value error, created_at__lt must be later in time than created_at__ge",
                }
            ]
        },
    )


@recipient_invoice_role_parametrization
async def test_recipient_invoices_listing_invalid_total_range(
    faker: Faker,
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
) -> None:
    total__le = faker.random_int()

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}/recipient-invoices/searches/",
            json={
                "filters": {
                    "total__ge": total__le + faker.random_int(min=1),
                    "total__le": total__le,
                }
            },
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body", "filters"],
                    "msg": "Value error, total__le must be greater than or equal to total__ge",
                }
            ]
        },
    )
