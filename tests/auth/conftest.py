import pytest

from src.auth import bootstrap
from src.auth.services import unit_of_work
from tests.fakes import auth
from src import config

DEFAULT_USER, DEFAULT_PWD = config.default_user()


@pytest.fixture()
def fake_dependencies():
    uow = auth.FakeUserUnitOfWork()
    email_sender = auth.FakeEmailSender()
    yield bootstrap.create(uow=uow, email_sender=email_sender)


@pytest.fixture()
def dependencies():
    yield bootstrap.create()


@pytest.fixture()
def uow():
    return unit_of_work.AuthSqlAlchemyUnitOfWork()
