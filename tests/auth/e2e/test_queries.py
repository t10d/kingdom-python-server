from tests.helpers import read_graphql
from tests.auth import helpers

from apolo import config

DEFAULT_USER, DEFAULT_PWD = config.default_user()

permission_queries = read_graphql("tests/auth/e2e/queries/permission.graphql")


def test_query_roles(auth_post, postgres_session_factory):
    response = auth_post(
        json=dict(query=permission_queries, operationName="roles"),
    )
    roles = response.json()["data"]["roles"]
    assert roles
    assert roles["elements"]
    assert all(
        [
            role["code"] and role["name"] and role["createdAt"]
            for role in roles["elements"]
        ]
    )

    count = helpers.query_roles_count(postgres_session_factory())
    assert roles["elementsCount"] == count


def test_query_specific_role(auth_post):
    response = auth_post(
        json=dict(
            query=permission_queries,
            operationName="role",
            variables=dict(code="test"),
        ),
    )
    role = response.json()["data"]["role"]
    assert role
    assert role["code"]
    assert role["name"]
    assert role["createdAt"]


def test_query_unknown_role(auth_post):
    response = auth_post(
        json=dict(
            query=permission_queries,
            operationName="role",
            variables=dict(code=helpers.random_word()),
        ),
    )
    role = response.json()["data"]["role"]
    assert role is None


def test_query_permissions(auth_post, postgres_session_factory):
    response = auth_post(
        json=dict(query=permission_queries, operationName="permissions"),
    )
    permissions = response.json()["data"]["permissions"]
    assert permissions
    assert permissions["elements"]
    assert all(
        [
            p["resource"] and p["action"] and p["isConditional"] is not None
            for p in permissions["elements"]
        ]
    )

    count = helpers.query_permissions_count(postgres_session_factory())
    assert permissions["elementsCount"] == count


def test_query_me(auth_post):
    response = auth_post(
        json=dict(
            query=permission_queries,
            operationName="me",
        ),
    )
    user = response.json()["data"]["me"]
    assert user["accessKey"] == DEFAULT_USER
    assert all(
        [
            user["name"] is not None
            and user["email"] is not None
            and user["createdAt"] is not None
            and len(user["permissions"]) > 0
            and user["role"]["name"] is not None
            and user["role"]["code"] is not None
        ]
    )


def test_query_known_user(auth_post):
    response = auth_post(
        json=dict(
            query=permission_queries,
            operationName="user",
            variables=dict(accessKey=DEFAULT_USER),
        ),
    )
    user = response.json()["data"]["user"]
    assert user["accessKey"] == DEFAULT_USER
    assert all(
        [
            user["name"] is not None
            and user["email"] is not None
            and user["createdAt"] is not None
            and len(user["permissions"]) > 0
            and user["role"]["name"] is not None
            and user["role"]["code"] is not None
        ]
    )


def test_query_unknown_user(auth_post):
    response = auth_post(
        json=dict(
            query=permission_queries,
            operationName="user",
            variables=dict(accessKey=helpers.random_username()),
        ),
    )
    user = response.json()["data"]["user"]
    assert user is None


def test_query_users(auth_post, postgres_session_factory):
    response = auth_post(
        json=dict(query=permission_queries, operationName="users"),
    )
    users = response.json()["data"]["users"]
    assert users
    assert users["elements"]
    assert all(
        [
            user["name"]
            and user["email"]
            and user["accessKey"]
            and user["createdAt"] is not None
            for user in users["elements"]
        ]
    )

    count = helpers.query_users_count(postgres_session_factory())
    assert users["elementsCount"] == count
