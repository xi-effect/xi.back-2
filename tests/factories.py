from polyfactory import Use

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.autocomplete_sch import SubjectSchema
from app.common.schemas.user_contacts_sch import UserContactSchema
from app.common.schemas.users_sch import UserProfileSchema
from app.common.schemas.vacancy_form_sch import VacancyFormSchema
from tests.common.id_provider import IDProvider
from tests.common.polyfactory_ext import BaseModelFactory


class SubjectFactory(BaseModelFactory[SubjectSchema]):
    __model__ = SubjectSchema


class VacancyFormWithMessageSchema(VacancyFormSchema):
    message: str


class VacancyFormWithMessageFactory(BaseModelFactory[VacancyFormWithMessageSchema]):
    __model__ = VacancyFormWithMessageSchema


class ProxyAuthDataFactory(BaseModelFactory[ProxyAuthData]):
    __model__ = ProxyAuthData

    user_id_provider = IDProvider()

    user_id = Use(user_id_provider.generate_id)


class UserProfileFactory(BaseModelFactory[UserProfileSchema]):
    __model__ = UserProfileSchema


class UserContactFactory(BaseModelFactory[UserContactSchema]):
    __model__ = UserContactSchema
