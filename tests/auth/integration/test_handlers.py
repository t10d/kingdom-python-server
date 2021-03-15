import pytest

from craftship.auth.domain import model
from craftship.auth.services import handlers
from tests.auth import helpers
from tests.fakes import auth
from apolo import config
from craftship.auth import utils

DEFAULT_USER, DEFAULT_PWD = config.default_user()


@pytest.mark.asyncio
async def test_create_user(fake_dependencies):
    uow, _ = fake_dependencies
    user = {
        "access_key": helpers.random_username(),
        "name": helpers.random_name(),
        "email": helpers.random_email(),
        "password": DEFAULT_PWD,
    }

    handlers.create_user(**user, uow=uow)

    assert len(uow.users.list()) > 0
    model_user = model.User(**user)
    assert uow.users.get(user["access_key"]) == model_user


@pytest.mark.asyncio
async def test_create_user_with_already_existent_user(
    fake_dependencies,
):
    uow, _ = fake_dependencies
    user = uow.users.list()[0]

    with pytest.raises(handlers.UserAlreadyExists):
        handlers.create_user(
            user.access_key, user.name, DEFAULT_PWD, user.name, uow
        )


@pytest.mark.asyncio
async def test_create_user_with_invalid_email(fake_dependencies):
    uow, _ = fake_dependencies
    user = {
        "access_key": helpers.random_username(),
        "name": helpers.random_name(),
        "email": "invalid_email",
        "password": helpers.random_password(),
    }

    with pytest.raises(handlers.InvalidEmail):
        handlers.create_user(**user, uow=uow)


@pytest.mark.asyncio
async def test_authenticate_user(fake_dependencies) -> None:
    uow, _ = fake_dependencies
    user = uow.users.list()[0]

    token = handlers.authenticate_user(
        access_key=user.access_key, password=DEFAULT_PWD, uow=uow
    )
    assert len(token.split(".")) == 3


@pytest.mark.asyncio
async def test_authenticate_unknow_user(fake_dependencies) -> None:
    uow, _ = fake_dependencies
    with pytest.raises(handlers.UnknownUser):
        handlers.authenticate_user(
            access_key="unknow_user", password=DEFAULT_PWD, uow=uow
        )


@pytest.mark.asyncio
async def test_authenticate_wrong_password(fake_dependencies) -> None:
    uow, _ = fake_dependencies
    user = uow.users.list()[0]
    with pytest.raises(handlers.WrongCredentials):
        handlers.authenticate_user(
            access_key=user.access_key, password="wrong_password", uow=uow
        )


@pytest.mark.asyncio
async def test_create_role(fake_dependencies):
    uow, _ = fake_dependencies
    handlers.create_role(
        code=helpers.DEFAULT_ROLE_CODE,
        name=helpers.DEFAULT_ROLE_NAME,
        permissions=auth.AVAILABLE_PERMISSIONS[:2],
        uow=uow,
    )
    assert uow.roles.get(helpers.DEFAULT_ROLE_CODE)


@pytest.mark.asyncio
async def test_create_role_with_already_existent_code(fake_dependencies):
    uow, _ = fake_dependencies
    with pytest.raises(handlers.RoleAlreadyExists):
        handlers.create_role(
            code=helpers.DEFAULT_ROLE_CODE,
            name=helpers.DEFAULT_ROLE_NAME,
            permissions=[],
            uow=uow,
        )


@pytest.mark.asyncio
async def test_attach_permissions_to_role(fake_dependencies):
    uow, _ = fake_dependencies
    permissions_i = uow.roles.get(helpers.DEFAULT_ROLE_CODE).permissions
    handlers.attach_permissions_to_role(
        code=helpers.DEFAULT_ROLE_CODE,
        permissions=auth.AVAILABLE_PERMISSIONS[2:4],
        uow=uow,
    )

    permissions_j = uow.roles.get(helpers.DEFAULT_ROLE_CODE).permissions
    assert permissions_i != permissions_j
    assert model.Permission(**auth.AVAILABLE_PERMISSIONS[2]) in permissions_j
    assert model.Permission(**auth.AVAILABLE_PERMISSIONS[3]) in permissions_j


@pytest.mark.asyncio
async def test_detach_permissions_from_role(fake_dependencies):
    uow, _ = fake_dependencies
    permissions_i = uow.roles.get(helpers.DEFAULT_ROLE_CODE).permissions
    handlers.detach_permissions_from_role(
        code=helpers.DEFAULT_ROLE_CODE,
        permissions=auth.AVAILABLE_PERMISSIONS[2:4],
        uow=uow,
    )

    permissions_j = uow.roles.get(helpers.DEFAULT_ROLE_CODE).permissions
    assert permissions_i != permissions_j
    assert (
        model.Permission(**auth.AVAILABLE_PERMISSIONS[2]) not in permissions_j
    )
    assert (
        model.Permission(**auth.AVAILABLE_PERMISSIONS[3]) not in permissions_j
    )


@pytest.mark.asyncio
async def test_reset_pwd_unknow_user(fake_dependencies) -> None:
    uow, email_sender = fake_dependencies
    with pytest.raises(handlers.UnknownUser):
        handlers.reset_password(
            access_key="unknow_user",
            client_url="http://localhost:3000/",
            uow=uow,
            email_sender=email_sender,
        )


@pytest.mark.asyncio
async def test_reset_pwd_know_user(fake_dependencies) -> None:
    uow, email_sender = fake_dependencies
    user = uow.users.list()[0]
    assert email_sender.sent is False
    handlers.reset_password(
        access_key=user.access_key,
        client_url="http://localhost:3000/",
        uow=uow,
        email_sender=email_sender,
    )
    assert email_sender.sent is True


@pytest.mark.asyncio
async def test_wrong_token_change_user_pwd(fake_dependencies) -> None:
    uow, _ = fake_dependencies
    user = uow.users.list()[0]
    token = user.pack_authentication_secret()
    with pytest.raises(utils.InvalidToken):
        handlers.change_password(
            token=token, new_password=helpers.random_password(), uow=uow
        )


@pytest.mark.asyncio
async def test_wrong_pwd_change_user_pwd(fake_dependencies) -> None:
    uow, _ = fake_dependencies
    user = uow.users.list()[0]
    token = user.generate_password_reset_token()
    user.password = helpers.random_password()
    with pytest.raises(utils.InvalidToken):
        handlers.change_password(
            token=token, new_password=helpers.random_password(), uow=uow
        )


@pytest.mark.asyncio
async def test_correct_pwd_change_user_pwd(fake_dependencies) -> None:
    uow, _ = fake_dependencies
    user = uow.users.list()[0]
    token = user.generate_password_reset_token()
    new_password = helpers.random_password()
    handlers.change_password(token=token, new_password=new_password, uow=uow)
    assert user.is_correct_password(new_password)


@pytest.mark.asyncio
async def test_pwd_change_unknow_user(fake_dependencies) -> None:
    uow, _ = fake_dependencies
    user = uow.users.list()[0]
    token = user.generate_password_reset_token()
    user.access_key = helpers.random_username()
    with pytest.raises(handlers.UnknownUser):
        handlers.change_password(
            token=token, new_password=helpers.random_password(), uow=uow
        )


@pytest.mark.asyncio
async def test_attach_permissions_to_user(fake_dependencies):
    uow, _ = fake_dependencies
    user = uow.users.list()[0]
    permissions_i = user.permissions

    handlers.attach_permissions_to_user(
        access_key=user.access_key,
        permissions=auth.AVAILABLE_PERMISSIONS[2:4],
        uow=uow,
    )

    permissions_j = uow.users.get(user.access_key).permissions
    assert permissions_i != permissions_j
    assert model.Permission(**auth.AVAILABLE_PERMISSIONS[2]) in permissions_j
    assert model.Permission(**auth.AVAILABLE_PERMISSIONS[3]) in permissions_j


@pytest.mark.asyncio
async def test_detach_permissions_from_user(fake_dependencies):
    uow, _ = fake_dependencies
    user = uow.users.list()[0]
    permissions_i = user.permissions
    handlers.detach_permissions_from_user(
        access_key=user.access_key,
        permissions=auth.AVAILABLE_PERMISSIONS[2:4],
        uow=uow,
    )

    permissions_j = uow.users.get(user.access_key).permissions
    assert permissions_i != permissions_j
    assert (
        model.Permission(**auth.AVAILABLE_PERMISSIONS[2]) not in permissions_j
    )
    assert (
        model.Permission(**auth.AVAILABLE_PERMISSIONS[3]) not in permissions_j
    )


@pytest.mark.asyncio
async def test_set_user_role(fake_dependencies):
    uow, _ = fake_dependencies
    user = uow.users.list()[0]
    role = uow.roles.list()[0]

    user.detach_permissions(user.permissions)
    assert not user.permissions
    assert not user.role
    handlers.set_user_role(
        user_access_key=user.access_key,
        role_code=role.code,
        override_permissions=True,
        uow=uow,
    )

    assert user.role == role
    assert user.permissions == role.permissions


@pytest.mark.asyncio
async def test_verify_permission_user_without_permission(
    fake_dependencies,
):
    uow, _ = fake_dependencies
    access_key = helpers.random_username()
    handlers.create_user(
        access_key=access_key,
        name=helpers.random_name(),
        email=helpers.random_email(),
        password=helpers.random_password(),
        uow=uow,
    )

    with pytest.raises(handlers.NotAllowed):
        handlers.verify_user_permission(
            access_key=access_key, resource="user", action="CREATE", uow=uow
        )


@pytest.mark.asyncio
async def test_verify_permission_user_with_permission(
    fake_dependencies,
):
    uow, _ = fake_dependencies
    user = uow.users.list()[-1]
    handlers.attach_permissions_to_user(
        access_key=user.access_key,
        permissions=[auth.AVAILABLE_PERMISSIONS[0]],
        uow=uow,
    )

    permission = handlers.verify_user_permission(
        access_key=user.access_key,
        resource=auth.AVAILABLE_PERMISSIONS[0]["resource"],
        action=auth.AVAILABLE_PERMISSIONS[0]["action"],
        uow=uow,
    )
    assert permission
