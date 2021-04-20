from dataclasses import dataclass
from typing import Dict, List, Tuple, TypeVar

from kingdom.access import jwt
from kingdom.access.base import Optional, Permission, Resource
from kingdom.access.dsl import TOKEN_ALL
from kingdom.access.types import (
    JWT,
    AuthResponse,
    Payload,
    PolicyContext,
    Scope,
    UserKey,
)


class AccessRequest:
    operation: int
    resource: str
    selector: str

    def __init__(self, operation: str, resource: str, selector: str) -> None:
        self.resource = resource
        self.selector = selector or TOKEN_ALL
        self.__operation = getattr(Permission, operation)
        self.operation = self.__operation.value

    def __repr__(self) -> str:
        return (
            f"<AccessRequest {self.__operation.name} on {self.selector} "
            f"of {self.resource}>"
        )


class NotEnoughPrivilegesErr(Exception):
    def __init__(self, request: AccessRequest):
        super().__init__(
            f"Unauthorized: User have not enough privileges to do "
            f"{request.operation} on {request.selector} of {request.resource}."
        )


def authenticate(token: JWT) -> AuthResponse:
    """
    Checks if a subject, identified by a JWT, is a recognized and trusted
    entity.

    Outputs:
        AuthResponse, if subject is allowed in.
        Exception, if credentials (JWT) are not accepted.
    """
    payload = jwt.decode(token)
    return payload["policies"], payload["access_key"]


def authorize(
    context: PolicyContext, resource: str, operation: str, selector: str = "",
) -> Scope:
    """
    Checks if, given a subject `context`, if system allows it to `operate` on
    instance `selector` of `resource`.

    Outputs:
        Scope, list of resource identifiers that subject is allowed to
                perform asked operation.
        Exception, if subject is not authorized to perform asked operation.
    """
    request = AccessRequest(
        resource=resource, operation=operation, selector=selector
    )
    scope, authorized = check_permission(context, request)
    if not authorized:
        raise NotEnoughPrivilegesErr(request)
    return scope


def check_permission(
    owned_policies: PolicyContext, access_request: AccessRequest
) -> Tuple[Scope, bool]:
    """
    When checking permissions, behaviour differs by the nature of requested
    operation:

    If it's a
    - READ, scope acts as access control, and passes to the system
    which instances of given resource the subject is allowed to read.
    Obs.: In this case, is_allowed is always True.

    - WRITE, is_allowed tells if user can perform that WRITE operation. Acts
    as a circuit breaker, as it is a all-or-nothing operation.
    Obs.: In this case, scope is always [access_request.selector]
    """
    if access_request.operation == Permission.READ.value:
        return get_read_scope(owned_policies, access_request), True
    return (
        [access_request.selector],
        is_write_allowed(owned_policies, access_request),
    )


def get_read_scope(
    owned_policies: PolicyContext, access_request: AccessRequest
) -> Scope:
    """
    Consider a subject that tries to access a resource. The access attempt is
    abstracted as AccessRequest and the whole set of policies it owns is
    represented as PolicyContext.

    This function returns which selectors of access_request.resource the
    subject is allowed to read from.

    >>> access_request = AccessRequest(
        operation="READ", resource="coupon", selector="*"
    )
    >>> owned_perm = {
        "coupon": {
            "ab4c": Permission.READ.value,
            "bc3f": (Permission.READ | Permission.UPDATE),
        },
        "users": {
            "ccf3": Permission.READ.value,
            "abbc": (Permission.UPDATE | Permission.DELETE),
        },
    }
    >>> check_read_permission(owned_perm, access_request)
    ["ab4c", "bc3f"]

    More examples on test suite.
    """
    # Sanity check
    assert access_request.operation == Permission.READ.value

    resource = access_request.resource
    if resource not in owned_policies:
        # Subject has no permission related to requested resource.
        return []

    # Subject has at least one selector that it can read.
    if TOKEN_ALL in owned_policies[resource]:
        # If it has any binding to "*", then it can read it all.
        return [TOKEN_ALL]

    # Subject has specific selectors, we shall return them.
    allowed_ids = owned_policies[resource].keys()
    return list(allowed_ids)


def is_write_allowed(
    owned_policies: PolicyContext, access_request: AccessRequest,
) -> bool:
    """
    Consider a subject that tries to access a resource. The access attempt is
    abstracted as AccessRequest and the whole set of policies it owns is
    represented as PolicyContext.

    This function returns whether the user has enough permissions to do
    the write operation on AccessRequest.

    >>> access_request = AccessRequest(
        operation=Permission.CREATE, resource=Resource("Coupon"), selector="*"
    )
    >>> owned_perm = {
        "coupon": {
            "ab4c": (Permission.READ.value,),
            "bc3f": (Permission.READ | Permission.UPDATE),
            "cc4a": (Permission.UPDATE.value,),
            "b4a3": (Permission.DELETE.value,),
        },
    }
    >>> check_write_permission(owned_perm, access_request)
    False

    More examples on test suite.
    """

    def mask_pass(owned_permissions: int, requested_operation: int,) -> bool:
        """
        Calculates whether the requested operation is allowed on a set of owned
        permissions.

        >>> owned_perm = (
            Permission.READ | Permission.UPDATE | Permission.DELETE
        ),
        >>> requested_op = Permission.CREATE.value
        >>> is_allowed(owned_perm, requested_op)
        False
        """
        return bool(owned_permissions & requested_operation)

    assert access_request.operation & (
        Permission.CREATE | Permission.UPDATE | Permission.DELETE
    )

    resource = access_request.resource
    operation = access_request.operation
    if resource not in owned_policies:
        # Resource is unknown to subject.
        return False

    permissions = owned_policies[resource].get(access_request.selector, 0)

    if TOKEN_ALL in owned_policies[resource]:
        # We might be asking for a specific instance but we have a "*" policy
        # that contemplates it.
        if mask_pass(owned_policies[resource][TOKEN_ALL], operation):
            return True

    return mask_pass(permissions, operation)
