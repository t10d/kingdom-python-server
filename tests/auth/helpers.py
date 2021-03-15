import random
from faker import Faker

from apolo import config
from tests.fakes import auth

DEFAULT_ROLE_CODE, DEFAULT_ROLE_NAME = config.default_role()

TEST_USER_ACCESS_KEY = "test@npl.com.br"
TEST_USER_EMAIL = "email_falso_npl@npl.com.br"


def random_sha256() -> str:
    return Faker().sha256()


def random_name() -> str:
    return Faker().name()


def random_username() -> str:
    return Faker().user_name()


def random_email() -> str:
    return random.choice(
        [
            Faker().ascii_company_email,
            Faker().ascii_email,
            Faker().ascii_free_email,
            Faker().ascii_safe_email,
        ]
    )()


def random_password() -> str:
    return str(Faker().password())


def query_user_by_access_key(session, access_key):
    [user] = session.execute(
        "SELECT * FROM users WHERE access_key = :access_key",
        dict(access_key=access_key),
    )
    return user


def query_role_by_code(session, code):
    [role] = session.execute(
        "SELECT * FROM roles WHERE code = :code",
        dict(code=code),
    )
    return role


def query_role_permissions(session, code):
    permissions = session.execute(
        "SELECT p.* FROM roles r "
        "LEFT JOIN role_permissions rp ON r.id = rp.id_role "
        "LEFT JOIN permissions p ON rp.id_permission = p.id "
        "WHERE r.code = :code",
        dict(code=code),
    )
    return [dict(p) for p in permissions]


def random_word():
    return Faker().word()


def random_role():
    return {
        "code": random_word() + random_word(),
        "name": random_word(),
    }


def query_roles_count(session):
    [(count,)] = session.execute("SELECT COUNT(*) FROM roles")
    return count


def query_permissions_count(session):
    [(count,)] = session.execute("SELECT COUNT(*) FROM permissions")
    return count


def query_users_count(session):
    [(count,)] = session.execute("SELECT COUNT(*) FROM users")
    return count
