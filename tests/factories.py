from app.common.schemas.vacancy_form_sch import VacancyFormSchema
from tests.common.polyfactory_ext import BaseModelFactory


class VacancyFormWithMessageSchema(VacancyFormSchema):
    message: str


class VacancyFormWithMessageFactory(BaseModelFactory[VacancyFormWithMessageSchema]):
    __model__ = VacancyFormWithMessageSchema
