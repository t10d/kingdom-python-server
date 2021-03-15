from tests.helpers import read_graphql
from apolo import config
from tests.auth import helpers
from tests.fakes import auth

DEFAULT_USER, DEFAULT_PWD = config.default_user()


def test_create_user(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/create_user.graphql")
    command = {
        "accessKey": helpers.TEST_USER_ACCESS_KEY,
        "name": helpers.random_name(),
        "email": helpers.TEST_USER_EMAIL,
        "password": helpers.random_password(),
    }

    response = auth_post(
        json=dict(
            query=mutation,
            operationName="createUser",
            variables=dict(command=command),
        )
    )
    command_response = response.json()["data"]["createUser"]
    assert command_response
    assert "user_created" in command_response["status"].lower()


def test_create_user_without_token(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/create_user.graphql")
    command = {
        "accessKey": helpers.random_username(),
        "name": helpers.random_name(),
        "email": helpers.random_email(),
        "password": helpers.random_password(),
    }

    response = starlette_client.post(
        "/",
        json=dict(
            query=mutation,
            operationName="createUser",
            variables=dict(command=command),
        ),
    )

    errors = response.json()["errors"]
    assert len(errors) > 0
    assert (
        "Authorization directives missing from HTTP header"
        in errors[0]["message"]
    )
    assert "missing_auth_header" in errors[0]["extensions"]["status"].lower()


def test_create_user_with_existing_key(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/create_user.graphql")
    command = {
        "accessKey": DEFAULT_USER,
        "name": "test",
        "email": "test@nplbrasil.com.br",
        "password": "test",
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="createUser",
            variables=dict(command=command),
        )
    )

    errors = response.json()["errors"]
    assert errors
    assert "user_already_exists" in errors[0]["extensions"]["status"].lower()


def test_create_user_with_invalid_email(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/create_user.graphql")
    command = {
        "accessKey": "test_email@nplbrasil.com.br",
        "name": "test",
        "email": "test",
        "password": "test",
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="createUser",
            variables=dict(command=command),
        )
    )
    errors = response.json()["errors"]
    assert errors
    assert "invalid_email" in errors[0]["extensions"]["status"].lower()


def test_authentication_wrong_credentials(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/login_user.graphql")
    command = {
        "accessKey": DEFAULT_USER,
        "password": "wrong_password",
    }
    response = starlette_client.post(
        "/",
        json=dict(
            query=mutation,
            operationName="authenticate",
            variables=dict(command=command),
        ),
    )

    errors = response.json()["errors"]
    assert errors
    assert "wrong_credentials" in errors[0]["extensions"]["status"].lower()


def test_authentication_unknown_user(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/login_user.graphql")
    command = {
        "accessKey": "unknown_user",
        "password": "wrong_password",
    }
    response = starlette_client.post(
        "/",
        json=dict(
            query=mutation,
            operationName="authenticate",
            variables=dict(command=command),
        ),
    )

    errors = response.json()["errors"]
    assert errors
    assert "user_not_found" in errors[0]["extensions"]["status"].lower()


def test_authentication_known_user(starlette_client):
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
    assert token
    assert auth_type


def test_reset_pwd_known_user(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/reset_pwd.graphql")
    command = {"accessKey": helpers.TEST_USER_ACCESS_KEY}
    response = starlette_client.post(
        "/",
        json=dict(
            query=mutation,
            operationName="resetPassword",
            variables=dict(command=command),
        ),
    )
    status = response.json()["data"]["resetPassword"]["status"]
    message = response.json()["data"]["resetPassword"]["message"]
    assert "EMAIL_RESET_PWD_SENT" == status
    assert command["accessKey"] in message


def test_reset_pwd_unknown_user(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/reset_pwd.graphql")
    command = {
        "accessKey": "unknown_user",
    }
    response = starlette_client.post(
        "/",
        json=dict(
            query=mutation,
            operationName="resetPassword",
            variables=dict(command=command),
        ),
    )
    errors = response.json()["errors"]
    assert errors
    assert "user_not_found" in errors[0]["extensions"]["status"].lower()


def test_change_pwd_valid_token(starlette_client, uow):
    mutation = read_graphql("tests/auth/e2e/queries/change_pwd.graphql")

    with uow:
        user = uow.users.get(helpers.TEST_USER_ACCESS_KEY)
        token = user.generate_password_reset_token()
        new_password = helpers.random_password()
        command = {
            "token": token,
            "newPassword": new_password,
        }
        response = starlette_client.post(
            "/",
            json=dict(
                query=mutation,
                operationName="changePassword",
                variables=dict(command=command),
            ),
        )

    status = response.json()["data"]["changePassword"]["status"]
    message = response.json()["data"]["changePassword"]["message"]
    assert status == "PWD_CHANGED"
    assert message == "Password changed successfully"
    with uow:
        user = uow.users.get(helpers.TEST_USER_ACCESS_KEY)
        assert user.is_correct_password(new_password)


def test_change_pwd_invalid_token(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/change_pwd.graphql")
    command = {
        "token": "invalid_token",
        "newPassword": helpers.random_password(),
    }
    response = starlette_client.post(
        "/",
        json=dict(
            query=mutation,
            operationName="changePassword",
            variables=dict(command=command),
        ),
    )
    errors = response.json()["errors"]
    assert errors
    assert "invalid_token" in errors[0]["extensions"]["status"].lower()


def test_create_role_without_permissions(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    code = helpers.random_word()
    command = {
        "code": code,
        "name": code,
    }

    response = auth_post(
        json=dict(
            query=mutation,
            operationName="createRole",
            variables=dict(command=command),
        ),
    )

    command_response = response.json()["data"]["createRole"]
    assert command_response
    assert "role_created" in command_response["status"].lower()


def test_create_role_with_permissions(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "code": helpers.DEFAULT_ROLE_CODE,
        "name": helpers.DEFAULT_ROLE_NAME,
        "permissions": [auth.AVAILABLE_PERMISSIONS_GRAPHQL[0]],
    }

    response = auth_post(
        json=dict(
            query=mutation,
            operationName="createRole",
            variables=dict(command=command),
        ),
    )

    command_response = response.json()["data"]["createRole"]
    assert command_response
    assert "role_created" in command_response["status"].lower()


def test_create_role_with_existing_code(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "code": helpers.DEFAULT_ROLE_CODE,
        "name": helpers.random_word(),
        "permissions": [],
    }

    response = auth_post(
        json=dict(
            query=mutation,
            operationName="createRole",
            variables=dict(command=command),
        ),
    )
    errors = response.json()["errors"]
    assert errors
    assert "role_already_exist" in errors[0]["extensions"]["status"].lower()


def test_attach_role_permissions(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "code": helpers.DEFAULT_ROLE_CODE,
        "permissions": [
            auth.AVAILABLE_PERMISSIONS_GRAPHQL[1],
            auth.AVAILABLE_PERMISSIONS_GRAPHQL[2],
        ],
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="attachRolePermissions",
            variables=dict(command=command),
        ),
    )
    command_response = response.json()["data"]["attachRolePermissions"]
    assert command_response
    assert "permissions_attached" in command_response["status"].lower()


def test_detach_role_permissions(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "code": helpers.DEFAULT_ROLE_CODE,
        "permissions": [
            auth.AVAILABLE_PERMISSIONS_GRAPHQL[1],
            auth.AVAILABLE_PERMISSIONS_GRAPHQL[2],
        ],
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="detachRolePermissions",
            variables=dict(command=command),
        ),
    )
    command_response = response.json()["data"]["detachRolePermissions"]
    assert command_response
    assert "permissions_detached" in command_response["status"].lower()


def test_attach_user_permissions(auth_post, uow):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "accessKey": helpers.TEST_USER_ACCESS_KEY,
        "permissions": [
            auth.AVAILABLE_PERMISSIONS_GRAPHQL[1],
            auth.AVAILABLE_PERMISSIONS_GRAPHQL[2],
        ],
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="attachUserPermissions",
            variables=dict(command=command),
        ),
    )
    command_response = response.json()["data"]["attachUserPermissions"]
    assert command_response
    assert "permissions_attached" in command_response["status"].lower()
    with uow:
        user = uow.users.get(helpers.TEST_USER_ACCESS_KEY)
        assert len(user.permissions) == 2


def test_detach_user_permissions(auth_post, uow):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "accessKey": helpers.TEST_USER_ACCESS_KEY,
        "permissions": [
            auth.AVAILABLE_PERMISSIONS_GRAPHQL[1],
            auth.AVAILABLE_PERMISSIONS_GRAPHQL[2],
        ],
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="detachUserPermissions",
            variables=dict(command=command),
        ),
    )
    command_response = response.json()["data"]["detachUserPermissions"]
    assert command_response
    assert "permissions_detached" in command_response["status"].lower()
    with uow:
        user = uow.users.get(helpers.TEST_USER_ACCESS_KEY)
        assert len(user.permissions) == 0


def test_set_user_role(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "userAccessKey": DEFAULT_USER,
        "roleCode": helpers.DEFAULT_ROLE_CODE,
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="setUserRole",
            variables=dict(command=command),
        ),
    )
    command_response = response.json()["data"]["setUserRole"]
    assert command_response
    assert "user_role_set" in command_response["status"].lower()


def test_set_user_role_with_nonexistent_user_or_role(auth_post):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "userAccessKey": helpers.random_word(),
        "roleCode": helpers.DEFAULT_ROLE_CODE,
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="setUserRole",
            variables=dict(command=command),
        ),
    )
    errors = response.json()["errors"]
    assert errors
    assert "user_not_found" in errors[0]["extensions"]["status"].lower()

    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "userAccessKey": DEFAULT_USER,
        "roleCode": helpers.random_word(),
    }
    response = auth_post(
        json=dict(
            query=mutation,
            operationName="setUserRole",
            variables=dict(command=command),
        ),
    )
    errors = response.json()["errors"]
    assert errors
    assert "role_not_found" in errors[0]["extensions"]["status"].lower()


def test_wrong_or_expired_token(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "userAccessKey": helpers.random_word(),
        "roleCode": helpers.DEFAULT_ROLE_CODE,
    }
    headers = dict(Authorization=f"bearer wrong.token.for_sure")
    response = starlette_client.post(
        json=dict(
            query=mutation,
            operationName="setUserRole",
            variables=dict(command=command),
        ),
        url="/",
        headers=headers,
    )
    errors = response.json()["errors"]
    assert errors
    assert "invalid_token" in errors[0]["extensions"]["status"].lower()


def test_wrong_scheme(starlette_client):
    mutation = read_graphql("tests/auth/e2e/queries/permission.graphql")
    command = {
        "userAccessKey": helpers.random_word(),
        "roleCode": helpers.DEFAULT_ROLE_CODE,
    }
    headers = dict(Authorization=f"not_bearer wrong.token.for_sure")
    response = starlette_client.post(
        json=dict(
            query=mutation,
            operationName="setUserRole",
            variables=dict(command=command),
        ),
        url="/",
        headers=headers,
    )
    errors = response.json()["errors"]
    assert errors
    assert "invalid_auth_schema" in errors[0]["extensions"]["status"].lower()
