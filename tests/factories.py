from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.autocomplete_sch import SubjectSchema
from app.common.schemas.users_sch import UserProfileSchema
from app.common.schemas.vacancy_form_sch import VacancyFormSchema
from tests.common.polyfactory_ext import BaseModelFactory


class SubjectFactory(BaseModelFactory[SubjectSchema]):
    __model__ = SubjectSchema


class VacancyFormWithMessageSchema(VacancyFormSchema):
    message: str


class VacancyFormWithMessageFactory(BaseModelFactory[VacancyFormWithMessageSchema]):
    __model__ = VacancyFormWithMessageSchema


class ProxyAuthDataFactory(BaseModelFactory[ProxyAuthData]):
    __model__ = ProxyAuthData


class UserProfileFactory(BaseModelFactory[UserProfileSchema]):
    __model__ = UserProfileSchema
