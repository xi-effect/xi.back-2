from app.notifications.models.user_contacts_db import UserContact
from tests.common.polyfactory_ext import BaseModelFactory


class UserContactInputFactory(BaseModelFactory[UserContact.InputSchema]):
    __model__ = UserContact.InputSchema
