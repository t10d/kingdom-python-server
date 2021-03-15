from typing import Dict, List, Tuple

from craftship.auth.domain import model
from craftship.auth.services import unit_of_work
from craftship.auth.adapters import email_sender
from craftship.auth import config
from craftship.auth import utils
from craftship.core.exceptions import ApoloException


class UnknownUser(ApoloException):
    def __init__(self, access_key: str):
        super().__init__(f"Access key {access_key} does not exist")


class UserAlreadyExists(ApoloException):
    def __init__(self, access_key: str):
        super().__init__(f"Access key {access_key} already exists")


class InvalidEmail(ApoloException):
    def __init__(self, email: str):
        super().__init__(f"Email {email} not valid")


class WrongCredentials(ApoloException):
    def __init__(self):
        super().__init__("Username or password invalid")


class RoleAlreadyExists(ApoloException):
    def __init__(self, code: str):
        super().__init__(f"Role with code {code} already exists")


class RoleNotFound(ApoloException):
    def __init__(self, code: str):
        super().__init__(f"Role with code {code} not found")


class NotAllowed(ApoloException):
    def __init__(self, access_key: str, action: str, resource: str):
        super().__init__(
            f"User {access_key} not allowed to perform action {action} on "
            f"resource {resource}"
        )


def change_password(
    token: str,
    new_password: str,
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
):
    decoded_token = utils.parse_token(token)
    access_key = decoded_token.get("access_key")
    old_password = decoded_token.get("sub")
    if not access_key or not old_password:
        raise utils.InvalidToken()

    with uow:
        user = uow.users.get(access_key)
        if not user:
            raise UnknownUser(access_key)

        if user.password != old_password:
            raise utils.InvalidToken()

        user.change_password(new_password=new_password)
        uow.commit()


def get_mapped_permissions(
    permissions: List[Dict], mapped_permissions: List[model.Permission]
):
    permissions = [model.Permission(**p) for p in permissions]
    return {mp for mp in mapped_permissions if mp in permissions}


def create_user(
    access_key: str,
    email: str,
    password: str,
    name: str,
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
) -> None:
    with uow:
        user = uow.users.get(access_key)
        if user:
            raise UserAlreadyExists(access_key)

        user = model.User(access_key, name, email, password)
        if not user.is_email_valid():
            raise InvalidEmail(email)

        uow.users.add(user)
        uow.commit()


def authenticate_user(
    access_key: str, password: str, uow: unit_of_work.AuthSqlAlchemyUnitOfWork
) -> str:
    with uow:
        user = uow.users.get(access_key)
        if not user:
            raise UnknownUser(access_key)

        if not user.is_correct_password(password):
            raise WrongCredentials()

        return user.pack_authentication_secret().decode("utf-8")


def reset_password(
    access_key: str,
    client_url: str,
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
    email_sender: email_sender.EmailSender,
):

    with uow:
        user = uow.users.get(access_key)
        if not user:
            raise UnknownUser(access_key)
        email_html = user.generate_reset_pwd_email(client_url=client_url)
        email_sender.send_email(
            email_to=user.email,
            subject=config.SUBJECT_PWD_CHANGE,
            template=email_html,
        )


def create_role(
    code: str,
    name: str,
    permissions: List[Dict],
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
):
    with uow:
        role = uow.roles.get(code)
        if role:
            raise RoleAlreadyExists(role.code)
        role = model.Role(
            code=code,
            name=name,
            permissions=get_mapped_permissions(
                permissions, uow.permissions.list()
            ),
        )
        uow.roles.add(role)
        uow.commit()


def attach_permissions_to_role(
    code: str,
    permissions: List[Dict],
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
):
    with uow:
        role = uow.roles.get(code)
        if not role:
            raise RoleNotFound(code)

        role.attach_permissions(
            get_mapped_permissions(permissions, uow.permissions.list()),
        )
        uow.commit()


def detach_permissions_from_role(
    code: str,
    permissions: List[Dict],
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
):
    with uow:
        role = uow.roles.get(code)
        if not role:
            raise RoleNotFound(code)

        role.detach_permissions(
            get_mapped_permissions(permissions, uow.permissions.list()),
        )
        uow.commit()


def attach_permissions_to_user(
    access_key: str,
    permissions: List[Dict],
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
):
    with uow:
        user: model.User = uow.users.get(access_key)
        if not user:
            raise UnknownUser(access_key)

        user.attach_permissions(
            get_mapped_permissions(permissions, uow.permissions.list())
        )
        uow.commit()


def detach_permissions_from_user(
    access_key: str,
    permissions: List[Dict],
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
):
    with uow:
        user: model.User = uow.users.get(access_key)
        if not user:
            raise UnknownUser(access_key)

        user.detach_permissions(
            get_mapped_permissions(permissions, uow.permissions.list())
        )
        uow.commit()


def set_user_role(
    user_access_key: str,
    role_code: str,
    override_permissions: bool,
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
):
    with uow:
        user: model.User = uow.users.get(user_access_key)
        if not user:
            raise UnknownUser(user_access_key)
        role: model.Role = uow.roles.get(role_code)
        if not role:
            raise RoleNotFound(role_code)
        user.set_role(role, override_permissions)
        uow.commit()


def verify_user_permission(
    access_key: str,
    action: str,
    resource: str,
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
):
    with uow:
        user: model.User = uow.users.get(access_key)
        if not user:
            raise UnknownUser(access_key)

        if not user.is_allowed_to(action, resource):
            raise NotAllowed(access_key, action, resource)

        return user.get_user_permission(action, resource)
