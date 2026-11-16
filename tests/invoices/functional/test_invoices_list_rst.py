from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from typing import Literal

import pytest
from faker import Faker
from pydantic import BaseModel
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
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
USER_COUNT = 3
CLASSROOM_COUNT = 2
RECIPIENT_INVOICES_PER_USER = len(PAYMENT_STATUSES) * len(PAYMENT_TYPES)
RECIPIENT_INVOICES_LIST_SIZE = RECIPIENT_INVOICES_PER_USER * USER_COUNT


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
    (
        "role",
        "authorized_client",
        "recipient_invoices",
        "response_schema",
        "classroom_index",
    ),
    [
        pytest.param(
            "tutor",
            lf("tutor_client"),
            lf("tutor_recipient_invoices"),
            RecipientInvoice.TutorResponseSchema,
            None,
            id="tutor",
        ),
        *[
            pytest.param(
                "tutor",
                lf("tutor_client"),
                lf("tutor_recipient_invoices"),
                RecipientInvoice.TutorResponseSchema,
                classroom_index,
                id=f"tutor_in_classroom_{classroom_index}",
            )
            for classroom_index in range(CLASSROOM_COUNT)
        ],
        pytest.param(
            "student",
            lf("student_client"),
            lf("student_recipient_invoices"),
            RecipientInvoice.StudentResponseSchema,
            None,
            id="student",
        ),
        *[
            pytest.param(
                "student",
                lf("student_client"),
                lf("student_recipient_invoices"),
                RecipientInvoice.StudentResponseSchema,
                classroom_index,
                id=f"student_in_classroom_{classroom_index}",
            )
            for classroom_index in range(CLASSROOM_COUNT)
        ],
    ],
)


@recipient_invoice_list_role_parametrization
@pytest.mark.parametrize(
    "filters",
    [
        pytest.param(None, id="omitted_filters"),
        pytest.param({}, id="empty_filters"),
    ],
)
@pytest.mark.parametrize(
    ("offset_share", "limit_share"),
    [
        pytest.param(Fraction(0), Fraction(1), id="start_to_end"),
        pytest.param(Fraction(0), Fraction(1, 2), id="start_to_middle"),
        pytest.param(Fraction(1, 2), Fraction(1), id="middle_to_end"),
    ],
)
async def test_recipient_invoices_listing(
    classroom_ids: Sequence[int],
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_index: int | None,
    filters: AnyJSON | None,
    offset_share: Fraction,
    limit_share: Fraction,
) -> None:
    classroom_id = None if classroom_index is None else classroom_ids[classroom_index]
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"
    listed_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if classroom_id is None or recipient_invoice.classroom_id == classroom_id
    ]
    offset = int(len(listed_recipient_invoices) * offset_share)
    limit = int(len(listed_recipient_invoices) * limit_share)
    cursor = None if offset == 0 else listed_recipient_invoices[offset - 1]

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}"
            f"{prefix}/recipient-invoices/searches/",
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
                listed_recipient_invoices[offset : offset + limit],
                response_schema,
            )
        ),
    )


@recipient_invoice_list_role_parametrization
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
    classroom_ids: Sequence[int],
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_index: int | None,
    statuses: set[PaymentStatus],
) -> None:
    classroom_id = None if classroom_index is None else classroom_ids[classroom_index]
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"
    listed_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if classroom_id is None or recipient_invoice.classroom_id == classroom_id
    ]

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
                    for recipient_invoice in listed_recipient_invoices
                    if recipient_invoice.status in statuses
                ],
                response_schema,
            )
        ),
    )


@recipient_invoice_list_role_parametrization
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
    classroom_ids: Sequence[int],
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_index: int | None,
    payment_types: set[PaymentType | None],
) -> None:
    classroom_id = None if classroom_index is None else classroom_ids[classroom_index]
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"
    listed_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if classroom_id is None or recipient_invoice.classroom_id == classroom_id
    ]

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
                    for recipient_invoice in listed_recipient_invoices
                    if recipient_invoice.payment_type in payment_types
                ],
                response_schema,
            )
        ),
    )


@pytest.mark.parametrize(
    "student_indexes",
    [
        *[
            pytest.param([student_index], id=f"student_{student_index}")
            for student_index in range(USER_COUNT)
        ],
        pytest.param(list(range(USER_COUNT)), id="all_students"),
    ],
)
async def test_tutor_recipient_invoices_listing_filtered_by_student_ids(
    tutor_client: TestClient,
    student_ids: Sequence[int],
    tutor_recipient_invoices: list[RecipientInvoice],
    student_indexes: list[int],
) -> None:
    filter_student_ids = {
        student_ids[student_index] for student_index in student_indexes
    }

    assert_response(
        tutor_client.post(
            "/api/protected/invoice-service/roles/tutor/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": {"student_id__in": list(filter_student_ids)},
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in tutor_recipient_invoices
                    if recipient_invoice.student_id in filter_student_ids
                ],
                RecipientInvoice.TutorResponseSchema,
            )
        ),
    )


@pytest.mark.parametrize(
    "tutor_indexes",
    [
        *[
            pytest.param([tutor_index], id=f"tutor_{tutor_index}")
            for tutor_index in range(USER_COUNT)
        ],
        pytest.param(list(range(USER_COUNT)), id="all_tutors"),
    ],
)
async def test_student_recipient_invoices_listing_filtered_by_tutor_ids(
    student_client: TestClient,
    tutor_ids: Sequence[int],
    student_recipient_invoices: list[RecipientInvoice],
    tutor_indexes: list[int],
) -> None:
    filter_tutor_ids = {tutor_ids[tutor_index] for tutor_index in tutor_indexes}

    assert_response(
        student_client.post(
            "/api/protected/invoice-service/roles/student/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": {"tutor_id__in": list(filter_tutor_ids)},
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in student_recipient_invoices
                    if recipient_invoice.tutor_id in filter_tutor_ids
                ],
                RecipientInvoice.StudentResponseSchema,
            )
        ),
    )


@recipient_invoice_list_role_parametrization
@pytest.mark.parametrize(
    ("lower_share", "upper_share"),
    [
        pytest.param(Fraction(1, 2), None, id="start_to_middle"),
        pytest.param(None, Fraction(1, 2), id="middle_to_end"),
        pytest.param(Fraction(1, 2), Fraction(1, 4), id="quarter_to_middle"),
    ],
)
async def test_recipient_invoices_listing_filtered_by_created_at(
    classroom_ids: Sequence[int],
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_index: int | None,
    lower_share: Fraction | None,
    upper_share: Fraction | None,
) -> None:
    classroom_id = None if classroom_index is None else classroom_ids[classroom_index]
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"
    listed_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if classroom_id is None or recipient_invoice.classroom_id == classroom_id
    ]
    created_at_ge = (
        None
        if lower_share is None
        else listed_recipient_invoices[
            int(len(listed_recipient_invoices) * lower_share)
        ].created_at
    )
    created_at_lt = (
        None
        if upper_share is None
        else listed_recipient_invoices[
            int(len(listed_recipient_invoices) * upper_share)
        ].created_at
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
                            None if created_at_ge is None else created_at_ge.isoformat()
                        ),
                        "created_at__lt": (
                            None if created_at_lt is None else created_at_lt.isoformat()
                        ),
                    }
                ),
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in listed_recipient_invoices
                    if (
                        created_at_ge is None
                        or recipient_invoice.created_at >= created_at_ge
                    )
                    and (
                        created_at_lt is None
                        or recipient_invoice.created_at < created_at_lt
                    )
                ],
                response_schema,
            )
        ),
    )


@recipient_invoice_list_role_parametrization
@pytest.mark.parametrize(
    ("lower_share", "upper_share"),
    [
        pytest.param(Fraction(1, 2), None, id="middle_to_end"),
        pytest.param(None, Fraction(1, 2), id="start_to_middle"),
        pytest.param(Fraction(1, 4), Fraction(1, 2), id="quarter_to_middle"),
        pytest.param(Fraction(1, 2), Fraction(1, 2), id="middle_to_middle"),
    ],
)
async def test_recipient_invoices_listing_filtered_by_total(
    classroom_ids: Sequence[int],
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    response_schema: type[BaseModel],
    classroom_index: int | None,
    lower_share: Fraction | None,
    upper_share: Fraction | None,
) -> None:
    classroom_id = None if classroom_index is None else classroom_ids[classroom_index]
    prefix = "" if classroom_id is None else f"/classrooms/{classroom_id}"
    listed_recipient_invoices = [
        recipient_invoice
        for recipient_invoice in recipient_invoices
        if classroom_id is None or recipient_invoice.classroom_id == classroom_id
    ]
    total_ge = (
        None
        if lower_share is None
        else listed_recipient_invoices[
            int(len(listed_recipient_invoices) * lower_share)
        ].total
    )
    total_le = (
        None
        if upper_share is None
        else listed_recipient_invoices[
            int(len(listed_recipient_invoices) * upper_share)
        ].total
    )

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}"
            f"{prefix}/recipient-invoices/searches/",
            json={
                "limit": RECIPIENT_INVOICES_LIST_SIZE,
                "filters": remove_none_values(
                    {
                        "total__ge": None if total_ge is None else str(total_ge),
                        "total__le": None if total_le is None else str(total_le),
                    }
                ),
            },
        ),
        expected_json=list(
            convert_recipient_invoices(
                [
                    recipient_invoice
                    for recipient_invoice in listed_recipient_invoices
                    if (total_ge is None or recipient_invoice.total >= total_ge)
                    and (total_le is None or recipient_invoice.total <= total_le)
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
@pytest.mark.parametrize(
    "upper_bound_offset",
    [
        pytest.param(-timedelta(hours=1), id="reversed_bounds"),
        pytest.param(timedelta(), id="equal_bounds"),
    ],
)
async def test_recipient_invoices_listing_filtered_by_invalid_created_at_range(
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
    upper_bound_offset: timedelta,
) -> None:
    created_at = datetime_utc_now()

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}/recipient-invoices/searches/",
            json={
                "filters": {
                    "created_at__ge": created_at.isoformat(),
                    "created_at__lt": (created_at + upper_bound_offset).isoformat(),
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
async def test_recipient_invoices_listing_filtered_by_invalid_total_range(
    role: Literal["tutor", "student"],
    authorized_client: TestClient,
) -> None:
    lower_total = Decimal(1)

    assert_response(
        authorized_client.post(
            f"/api/protected/invoice-service/roles/{role}/recipient-invoices/searches/",
            json={
                "filters": {
                    "total__ge": str(lower_total + 1),
                    "total__le": str(lower_total),
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
