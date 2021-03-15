import pytest
import functools
from starlette.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import engine, create_engine, MetaData
from sqlalchemy.orm import clear_mappers, sessionmaker
from sqlalchemy.orm.session import close_all_sessions
from tenacity import retry, stop_after_delay

from apolo import config
from craftship.federation import federation
from craftship.auth.services import unit_of_work
from craftship.auth.adapters import email_sender

from server.app import create_app
from serverless.app import Handler

from tests.helpers import read_graphql

DEFAULT_USER, DEFAULT_PWD = config.default_user()


@retry(stop=stop_after_delay(10))
def wait_for_engine_to_come_up(eng: engine.Engine) -> engine.Connection:
    return eng.connect()


@pytest.fixture
def starlette_client():
    app = create_app()
    client = TestClient(app)
    yield client


@pytest.fixture
def bcrypt():
    yield CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def uow():
    yield unit_of_work.AuthSqlAlchemyUnitOfWork()


@pytest.fixture(scope="session")
def orm_metadata():
    clear_mappers()
    metadata, _ = federation()
    yield metadata
    clear_mappers()


@pytest.fixture(scope="session")
def postgres_db(orm_metadata):
    engine = create_engine(
        config.get_postgres_uri(),
        isolation_level="READ_COMMITTED",
    )
    wait_for_engine_to_come_up(engine)
    orm_metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def postgres_session_factory(postgres_db: engine.Engine):
    yield sessionmaker(
        bind=postgres_db, autoflush=False
    )  # deliver to next fixture
    close_all_sessions()


@pytest.fixture()
def auth_post(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/login_user.graphql")
    command = {
        "accessKey": DEFAULT_USER,
        "password": DEFAULT_PWD,
    }
    response = starlette_client.post(
        "/",
        json=dict(
            query=mutation,
            operationName="authenticate",
            variables=dict(command=command),
        ),
    )
    token = response.json()["data"]["authenticate"]["token"]["value"]
    auth_type = response.json()["data"]["authenticate"]["token"]["authType"]
    headers = dict(Authorization=f"{auth_type} {token}")
    yield functools.partial(starlette_client.post, "/", headers=headers)


@pytest.fixture
def lambda_handler():
    handler = Handler(
        lambda: federation(start_orm=False)
    )
    return handler
