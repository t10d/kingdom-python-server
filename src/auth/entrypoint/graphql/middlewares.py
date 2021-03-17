from typing import Any, Dict, List, Set, Tuple
from ariadne.types import GraphQLError, GraphQLResolveInfo, Resolver
from starlette.requests import Headers, HTTPConnection

from src.auth import utils
from src.core.exceptions import resolve_error, ServerException


class MissingAuthHeader(ServerException):
    def __init__(self):
        super().__init__("Authorization directives missing from HTTP header")


class InvalidAuthSchema(ServerException):
    def __init__(self):
        super().__init__("Invalid authentication schema")


class HeaderMissingSomething(ServerException):
    def __init__(self):
        super().__init__("Invalid authentication schema")


ERROR_RESOLVER = {
    MissingAuthHeader: "MISSING_AUTH_HEADER",
    InvalidAuthSchema: "INVALID_AUTH_SCHEMA",
    HeaderMissingSomething: "HEADER_MISSING_SOMETHING",
    utils.InvalidToken: "INVALID_TOKEN",
}


def strip_token_from(headers: Headers) -> str:
    """Tries to strip it out a token from an HTTP request header
    Validates if everything is as expected"""
    if "Authorization" not in headers:
        raise MissingAuthHeader()

    auth_header: str = headers["Authorization"]
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise InvalidAuthSchema()
        return token
    except ValueError:
        raise HeaderMissingSomething()


def get_scope_and_user(request: HTTPConnection) -> Tuple[List[str], str]:
    """Tries to authenticate an incoming request"""
    token: str = strip_token_from(request.headers)
    payload: Dict[str, str] = utils.parse_token(token)
    access_key: str = payload["sub"]
    return ["authenticated"], access_key


def should_verify_auth(info: GraphQLResolveInfo) -> bool:
    """Whether there is a need to authenticate current request
    A request here is represented as request-resolve-info"""
    public_paths: Set = {
        "__schema",
        "authenticate",
        "resetPassword",
        "changePassword",
    }
    path_root, *rest = info.path.as_list()
    return not rest and path_root not in public_paths


def authentication_middleware(
    resolver: Resolver, obj: Any, info: GraphQLResolveInfo, **args
) -> Any:
    """Intercepts every resolving-call and tries to authenticate it"""
    if should_verify_auth(info) is False:
        return resolver(obj, info, **args)

    try:
        scope, access_key = get_scope_and_user(info.context["request"])
        info.context.update({"scope": scope, "access_key": access_key})
        return resolver(obj, info, **args)
    except Exception as error:
        return resolve_error(error, ERROR_RESOLVER)


middlewares = [authentication_middleware]
