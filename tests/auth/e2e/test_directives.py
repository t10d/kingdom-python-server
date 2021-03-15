from tests.helpers import read_graphql
from tests.auth import helpers
from apolo import config


def test_user_has_needed_permission_on_action(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/create_user.graphql")
    command = {
        "accessKey": helpers.random_username(),
        "name": helpers.random_name(),
        "email": helpers.random_email(),
        "password": helpers.random_password(),
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="createUser",
            variables=dict(command=command),
        )
    )
    status = response.json()["data"]["createUser"]["status"]
    assert "USER_CREATED" in status


def test_user_has_not_needed_permission_on_action(auth_post):
    permission_mutation = read_graphql(
        "tests/auth/e2e/queries/permission.graphql"
    )
    command = {
        "accessKey": config.default_user()[0],
        "permissions": [
            {"resource": "user", "action": "CREATE", "isConditional": False}
        ],
    }
    response = auth_post(
        json=dict(
            query=permission_mutation,
            operationName="detachUserPermissions",
            variables=dict(command=command),
        ),
    )
    status = response.json()["data"]["detachUserPermissions"]["status"]
    assert "PERMISSIONS_DETACHED" in status

    mutation = read_graphql("tests/auth/e2e/queries/create_user.graphql")
    command = {
        "accessKey": helpers.random_username(),
        "name": helpers.random_name(),
        "email": helpers.random_email(),
        "password": helpers.random_password(),
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="createUser",
            variables=dict(command=command),
        )
    )
    response = response.json()
    assert not response["data"]["createUser"]
    assert response["errors"]
    assert "not allowed" in response["errors"][0]["message"]

    permission_mutation = read_graphql(
        "tests/auth/e2e/queries/permission.graphql"
    )
    command = {
        "accessKey": config.default_user()[0],
        "permissions": [
            {"resource": "user", "action": "CREATE", "isConditional": False}
        ],
    }
    auth_post(
        json=dict(
            query=permission_mutation,
            operationName="attachUserPermissions",
            variables=dict(command=command),
        ),
    )
