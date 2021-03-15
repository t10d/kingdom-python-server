from src.auth.domain import model
from src.auth import utils

from tests.auth import helpers


def test_hashing_algorithm_is_correct(bcrypt):
    pwd = helpers.random_password()
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=pwd,
    )
    assert bcrypt.verify(pwd, user.password)


def test_new_user_hashes_password():
    pwd = helpers.random_password()
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=pwd,
    )
    assert not user.password == pwd
    assert user.is_correct_password(pwd)


def test_wrong_password():
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    assert not user.is_correct_password(helpers.random_password())


def test_invalid_email():
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email="test",
        password=helpers.random_password(),
    )
    assert not user.is_email_valid()


def test_user_equality():
    access_key = helpers.random_username()
    a_user = model.User(
        access_key=access_key,
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    b_user = model.User(
        access_key=access_key,
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    assert a_user == b_user


def test_attach_permissions():
    permission_1 = model.Permission(
        "wallet", model.PermissionActionEnum.CREATE.value, False
    )
    permission_2 = model.Permission(
        "wallet", model.PermissionActionEnum.CREATE.value, True
    )
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    user.attach_permissions({permission_1, permission_2})
    assert len(user.permissions) > 0
    assert user.permissions == {permission_1, permission_2}


def test_detach_permissions():
    permission_1 = model.Permission(
        resource="wallet",
        action=model.PermissionActionEnum.CREATE.value,
        is_conditional=False,
    )
    permission_2 = model.Permission(
        resource="wallet",
        action=model.PermissionActionEnum.CREATE.value,
        is_conditional=True,
    )
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    user.attach_permissions({permission_1, permission_2})
    assert len(user.permissions) == 2
    user.detach_permissions({permission_1})
    assert len(user.permissions) == 1


def test_set_user_role():
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    permission_1 = model.Permission(
        resource="wallet",
        action=model.PermissionActionEnum.CREATE.value,
        is_conditional=False,
    )
    user.attach_permissions({permission_1})
    assert user.permissions == {permission_1}

    permission_2 = model.Permission(
        resource="wallet",
        action=model.PermissionActionEnum.CREATE.value,
        is_conditional=True,
    )
    role = model.Role(
        name=helpers.DEFAULT_ROLE_NAME,
        code=helpers.DEFAULT_ROLE_CODE,
        permissions={permission_2},
    )
    user.set_role(role, override_permissions=True)
    assert user.role == role
    assert user.permissions == role.permissions


def test_token_reset_pwd() -> None:
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    token = user.generate_password_reset_token()
    decoded_token = utils.parse_token(token=token)
    old_pwd = decoded_token.get("sub")
    assert old_pwd
    assert decoded_token.get("access_key")
    assert old_pwd == user.password


# this test is to show that a auth token is different from a reset pwd one
def test_wrong_token_dont_reset_pwd() -> None:
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    # generates a auth token instead of a reset one
    token = user.pack_authentication_secret()
    decoded_token = utils.parse_token(token=token)
    # sub doesn't contain the hashed password
    assert decoded_token.get("sub") != user.password


def test_user_has_permission():
    user = model.User(
        access_key=helpers.random_username(),
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
    )
    assert not user.is_allowed_to(
        action=model.PermissionActionEnum.CREATE.value, resource="wallet"
    )

    permission_1 = model.Permission(
        resource="wallet",
        action=model.PermissionActionEnum.CREATE.value,
        is_conditional=False,
    )
    user.attach_permissions({permission_1})

    assert user.is_allowed_to(
        action=model.PermissionActionEnum.CREATE.value, resource="wallet"
    )
