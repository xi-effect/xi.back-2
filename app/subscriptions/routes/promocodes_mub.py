from collections.abc import Sequence
from typing import Annotated, Self

from fastapi import Query
from pydantic import model_validator
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.dependencies.promocodes_dep import PromocodeByCode, PromocodeByID
from app.subscriptions.models.promocodes_db import Promocode

router = APIRouterExt(tags=["promocodes mub"])


@router.get(
    "/promocodes/",
    response_model=list[Promocode.ResponseSchema],
    summary="List paginated promocodes",
)
async def list_promocodes(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> Sequence[Promocode]:
    return await Promocode.find_paginated_by_kwargs(
        offset, limit, Promocode.created_at.desc()
    )


class PromocodeInputSchema(Promocode.InputSchema):
    @model_validator(mode="after")
    def validate_promocode_valid_from_and_until_date(self) -> Self:
        if (
            self.valid_from is not None and self.valid_until is not None
        ) and self.valid_from >= self.valid_until:
            raise ValueError("the end date cannot be earlier than the start date")
        return self


class PromocodeConflictResponses(Responses):
    PROMOCODE_ALREADY_EXISTS = status.HTTP_409_CONFLICT, "Promocode already exists"


@router.post(
    "/promocodes/",
    status_code=status.HTTP_201_CREATED,
    response_model=Promocode.ResponseSchema,
    responses=PromocodeConflictResponses.responses(),
    summary="Create a new promocode",
)
async def create_promocode(data: PromocodeInputSchema) -> Promocode:
    if await Promocode.is_present_by_code(code=data.code):
        raise PromocodeConflictResponses.PROMOCODE_ALREADY_EXISTS
    return await Promocode.create(**data.model_dump())


@router.get(
    "/promocodes/by-id/{promocode_id}/",
    response_model=Promocode.ResponseSchema,
    summary="Retrieve any promocode by id",
)
async def retrieve_promocode_by_id(promocode: PromocodeByID) -> Promocode:
    return promocode


@router.get(
    "/promocodes/by-code/{code}/",
    response_model=Promocode.ResponseSchema,
    summary="Retrieve any promocode by code",
)
async def retrieve_promocode_by_code(promocode: PromocodeByCode) -> Promocode:
    return promocode


@router.put(
    "/promocodes/{promocode_id}/",
    response_model=Promocode.ResponseSchema,
    responses=PromocodeConflictResponses.responses(),
    summary="Update any promocode by id",
)
async def put_promocode(
    promocode: PromocodeByID,
    data: PromocodeInputSchema,
) -> Promocode:
    if data.code != promocode.code and await Promocode.is_present_by_code(
        code=data.code
    ):
        raise PromocodeConflictResponses.PROMOCODE_ALREADY_EXISTS
    promocode.update(**data.model_dump(), updated_at=datetime_utc_now())
    return promocode


@router.delete(
    "/promocodes/{promocode_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any promocode by id",
)
async def delete_promocode(promocode: PromocodeByID) -> None:
    await promocode.delete()
