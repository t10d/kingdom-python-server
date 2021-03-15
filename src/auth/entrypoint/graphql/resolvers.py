import logging
from typing import Union, Optional, Dict, Callable
from graphql import GraphQLError, GraphQLResolveInfo
from ariadne import (
    MutationType,
    QueryType,
    convert_kwargs_to_snake_case,
)

from craftship.core.exceptions import resolve_error
from craftship.auth.services import handlers
from craftship.auth.entrypoint import uow, email_sender
from craftship.auth import config, views
from craftship.auth import utils


query = QueryType()
mutation = MutationType()
bindings = (query, mutation)

ERROR_RESOLVER = {
    handlers.UnknownUser: "USER_NOT_FOUND",
    handlers.RoleNotFound: "ROLE_NOT_FOUND",
    handlers.RoleAlreadyExists: "ROLE_ALREADY_EXIST",
    utils.InvalidToken: "INVALID_TOKEN",
    handlers.InvalidEmail: "INVALID_EMAIL",
    handlers.UserAlreadyExists: "USER_ALREADY_EXISTS",
    handlers.WrongCredentials: "WRONG_CREDENTIALS",
}


def get_client_url(info: GraphQLResolveInfo) -> str:
    try:
        client_url = str(info.context["request"].client.host)
        return f"https://{client_url}/"
    except Exception as ex:
        logging.error(ex)
        raise AttributeError("Couldn't get base url to send email link")


def resolve_default(handler: Callable, response: Dict):
    @convert_kwargs_to_snake_case
    async def resolve(*_, command):
        try:
            handler(**command, uow=uow)
        except Exception as error:
            return resolve_error(error, ERROR_RESOLVER)
        return response

    return resolve


mutation.set_field(
    "createUser",
    resolve_default(
        handlers.create_user,
        dict(status="USER_CREATED", message="User successfully created"),
    ),
)
mutation.set_field(
    "changePassword",
    resolve_default(
        handlers.change_password,
        dict(status="PWD_CHANGED", message="Password changed successfully"),
    ),
)
mutation.set_field(
    "createRole",
    resolve_default(
        handlers.create_role,
        dict(status="ROLE_CREATED", message="Role successfully created"),
    ),
)
mutation.set_field(
    "attachRolePermissions",
    resolve_default(
        handlers.attach_permissions_to_role,
        dict(
            status="PERMISSIONS_ATTACHED",
            message="Permissions successfully attached to role",
        ),
    ),
)
mutation.set_field(
    "detachRolePermissions",
    resolve_default(
        handlers.detach_permissions_from_role,
        dict(
            status="PERMISSIONS_DETACHED",
            message="Permissions successfully detached from role",
        ),
    ),
)
mutation.set_field(
    "attachUserPermissions",
    resolve_default(
        handlers.attach_permissions_to_user,
        dict(
            status="PERMISSIONS_ATTACHED",
            message="Permissions successfully attached to user.",
        ),
    ),
)
mutation.set_field(
    "detachUserPermissions",
    resolve_default(
        handlers.detach_permissions_from_user,
        dict(
            status="PERMISSIONS_DETACHED",
            message="Permissions successfully detached from user.",
        ),
    ),
)
mutation.set_field(
    "setUserRole",
    resolve_default(
        handlers.set_user_role,
        dict(status="USER_ROLE_SET", message="Role successfully set to user."),
    ),
)


@mutation.field("authenticate")
@convert_kwargs_to_snake_case
async def resolve_authenticate(*_, command):
    try:
        token = handlers.authenticate_user(**command, uow=uow)
        user = views.query_user(uow, command["access_key"])
        user["token"] = dict(value=token, auth_type=config.AUTH_TYPE)
        return user
    except Exception as error:
        return resolve_error(error, ERROR_RESOLVER)


@mutation.field("resetPassword")
@convert_kwargs_to_snake_case
async def reset_password(_, info, command):
    client_url = get_client_url(info=info)
    try:
        handlers.reset_password(
            **command,
            client_url=client_url,
            uow=uow,
            email_sender=email_sender,
        )
    except Exception as error:
        return resolve_error(error, ERROR_RESOLVER)
    return {
        "status": "EMAIL_RESET_PWD_SENT",
        "message": f"Reset password email to {command['access_key']}",
    }


@query.field("role")
@convert_kwargs_to_snake_case
async def resolve_query_role(*_, code: str):
    return views.query_role(code, uow)


@query.field("roles")
@convert_kwargs_to_snake_case
async def resolve_query_roles(
    *_, name: str = "", pagination_info: Optional[Dict] = None
):
    return views.query_roles(
        uow=uow, pagination_info=pagination_info, name=name
    )


@query.field("permissions")
@convert_kwargs_to_snake_case
async def resolve_query_permissions(
    *_,
    resource: str = "",
    action: str = "",
    pagination_info: Optional[Dict] = None,
):
    return views.query_permissions(
        uow=uow,
        pagination_info=pagination_info,
        resource=resource,
        action=action,
    )


@query.field("me")
@convert_kwargs_to_snake_case
def resolve_me(_, info):
    access_key = info.context.get("access_key")
    return views.query_user(uow, access_key)


@query.field("user")
@convert_kwargs_to_snake_case
async def resolve_query_user(*_, access_key: str):
    return views.query_user(uow, access_key)


@query.field("users")
@convert_kwargs_to_snake_case
async def resolve_query_users(*_, pagination_info: Optional[Dict] = None):
    return views.query_users(uow=uow, pagination_info=pagination_info)
