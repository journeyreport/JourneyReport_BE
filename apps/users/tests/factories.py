import random
import factory
import factory.fuzzy

from faker import Faker
from factory.django import DjangoModelFactory


DEFAULT_PASSWORD = "password"
WRONG_PASSWORD = "wrong-password"

fake = Faker()


def get_lorem_ipsum(length=0):
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    if length:
        return text[:length]
    return text


def make_first_name():
    return fake.first_name()


def make_last_name():
    return fake.last_name()


def make_email():
    return f"{fake.first_name()}.{fake.last_name()}@example.com".lower()


def make_phone_number():
    codes = (50, 95, 99, 66, 67, 97, 96, 98, 68, 63, 93, 73, )
    return f"+380{random.choice(codes)}{random.randint(1000000, 9999999)}"

def make_articles_text():
    return get_lorem_ipsum(length=255)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = 'users.User'
        django_get_or_create = ('email',)

    first_name = factory.LazyAttribute(lambda x: make_first_name())
    last_name = factory.LazyAttribute(lambda x: make_last_name())
    email = factory.LazyAttribute(lambda x: make_email())
    password = factory.PostGenerationMethodCall('set_password', DEFAULT_PASSWORD)
    is_active = True
    is_admin = False


class BannedUserFactory(UserFactory):
    is_active = False


class AdminFactory(UserFactory):
    is_admin = True


class ContactFactory(UserFactory):
    class Meta:
        model = 'users.Contact'
        django_get_or_create = ('email',)

    is_registered = False


class PhoneNumberConfirmationFactory(DjangoModelFactory):
    class Meta:
        model = 'users.PhoneNumberConfirmation'

    user = factory.SubFactory(UserFactory)
    phone_number = factory.LazyAttribute(lambda x: make_phone_number())
