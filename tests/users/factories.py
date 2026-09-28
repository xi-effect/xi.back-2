from polyfactory import Use

from app.common.schemas.demo_form_sch import DemoFormSchema
from app.users.models.user_flag_kinds_db import UserFlagKind
from app.users.models.users_db import User
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory
from tests.users.utils import generate_username


class UserInputFactory(BaseModelFactory[User.InputSchema]):
    __model__ = User.InputSchema

    email = Use(BaseModelFactory.__faker__.email)
    username = Use(generate_username)
    password = Use(BaseModelFactory.__faker__.password)


class UserFullPatchFactory(BasePatchModelFactory[User.PatchMUBSchema]):
    __model__ = User.PatchMUBSchema

    email = Use(BaseModelFactory.__faker__.email)
    username = Use(generate_username)
    password = Use(BaseModelFactory.__faker__.password)


class DemoFormFactory(BaseModelFactory[DemoFormSchema]):
    __model__ = DemoFormSchema


class UserFlagKindInputFactory(BaseModelFactory[UserFlagKind.InputSchema]):
    __model__ = UserFlagKind.InputSchema

    key = Use(BaseModelFactory.__faker__.uuid4)


class UserFlagKindPatchFactory(BasePatchModelFactory[UserFlagKind.PatchSchema]):
    __model__ = UserFlagKind.PatchSchema

    key = Use(BaseModelFactory.__faker__.uuid4)
