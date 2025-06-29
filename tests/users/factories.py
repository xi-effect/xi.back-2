from polyfactory import Use

from app.common.schemas.demo_form_sch import DemoFormSchema
from app.users.models.users_db import User
from app.users.routes.password_reset_rst import ResetCredentials
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory
from tests.users.utils import generate_username


class UserInputFactory(BaseModelFactory[User.InputSchema]):
    __model__ = User.InputSchema

    email = Use(BaseModelFactory.__faker__.email)
    username = Use(generate_username)
    password = Use(BaseModelFactory.__faker__.password)


class UserFullPatchFactory(BasePatchModelFactory[User.FullPatchSchema]):
    __model__ = User.FullPatchSchema

    email = Use(BaseModelFactory.__faker__.email)
    username = Use(generate_username)
    password = Use(BaseModelFactory.__faker__.password)


class DemoFormFactory(BaseModelFactory[DemoFormSchema]):
    __model__ = DemoFormSchema


class ResetCredentialsFactory(BaseModelFactory[ResetCredentials]):
    __model__ = ResetCredentials
