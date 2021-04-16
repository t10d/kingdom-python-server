from dataclasses import dataclass
from typing import Dict, List, Tuple, TypeVar

from kingdom.access import jwt
from kingdom.access.base import Optional, Permission, Resource
from kingdom.access.types import (
    JWT,
    AuthResponse,
    Payload,
    PolicyContext,
    Scope,
    UserKey,
)

TOKEN_ALL = "*"


class AccessRequest:
    operation: int
    resource: str
    selector: str

    def __init__(self, operation: str, resource: str, selector: str) -> None:
        self.resource = resource
        self.selector = selector
        if not selector:
            self.selector = TOKEN_ALL
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
    Raises an Exception if not authenticated
    """
    payload = jwt.decode(token)
    return payload["policies"], payload["access_key"]


def authorize(
    policies: PolicyContext, resource: str, operation: str, selector: str = "",
) -> Scope:
    """
    Raises an Exception if not authorized
    """
    request = AccessRequest(
        resource=resource, operation=operation, selector=selector
    )
    scope, authorized = check_permission(policies, request)
    if not authorized:
        raise NotEnoughPrivilegesErr(request)
    return scope


def check_permission(
    owned_policies: PolicyContext, access_request: AccessRequest
) -> Tuple[Scope, bool]:
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
        When a subject tries to perform a write, this function calculates
        whether the requested operation is allowed on a set of owned
        permissions.

        >>> owned_perm = (
            Permission.READ | Permission.UPDATE | Permission.DELETE
        ),
        >>> requested_op = Permission.CREATE.value
        >>> is_allowed(owned_perm, requested_op)
        False
        """
        return int(owned_permissions & requested_operation) > 0

    TOKEN_ALL = "*"
    assert access_request.operation & (
        Permission.CREATE | Permission.UPDATE | Permission.DELETE
    )

    resource = access_request.resource
    operation = access_request.operation
    selector = access_request.selector
    if resource not in owned_policies:
        # Resource is unknown to subject.
        return False

    if selector == TOKEN_ALL and selector not in owned_policies[resource]:
        # For e.g CREATE without CREATE ALL policy
        return False

    if TOKEN_ALL in owned_policies[resource]:
        # We might be asking for a specific instance but we have a "*" policy
        # that contemplates it.
        if mask_pass(owned_policies[resource][TOKEN_ALL], operation):
            return True

    # Now that we've reached here, it means that subject has no "*" policy
    # to allow it for asked resource. Hence it must have a specific policy
    if selector not in owned_policies[resource]:
        return False

    permissions = owned_policies[resource][selector]
    return mask_pass(permissions, operation)