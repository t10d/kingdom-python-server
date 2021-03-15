from src.auth.domain import model
from src.auth.services import unit_of_work
from tests.auth import helpers
from tests.fakes import auth


def test_unit_of_work_can_persist_user(postgres_session_factory):
    user = {
        "access_key": helpers.random_username(),
        "name": helpers.random_name(),
        "email": helpers.random_email(),
        "password": helpers.random_password(),
    }
    model_user = model.User(**user)
    uow = unit_of_work.AuthSqlAlchemyUnitOfWork(postgres_session_factory)
    with uow:
        uow.users.add(model_user)
        uow.commit()

    session = postgres_session_factory()
    user = helpers.query_user_by_access_key(
        session, access_key=user["access_key"]
    )
    assert user


def test_unit_of_work_can_persist_role(postgres_session_factory):
    role = {
        "code": helpers.random_word(),
        "name": helpers.random_word(),
    }
    uow = unit_of_work.AuthSqlAlchemyUnitOfWork(postgres_session_factory)
    with uow:
        model_role = model.Role(
            **role, permissions=set(uow.permissions.list()[:1])
        )
        uow.roles.add(model_role)
        uow.commit()

    session = postgres_session_factory()
    role = helpers.query_role_by_code(session, role["code"])
    assert role
    permissions = helpers.query_role_permissions(session, role["code"])
    assert len(permissions) == 1
