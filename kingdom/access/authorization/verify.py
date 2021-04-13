"""
verify.py

Responsible for checking and handling whether a given subject is allowed to do
a given action on a given resource.

There are two authorization scenarios considered:
   1. A read scenario, in which authorization module should pass-along to
       the server which instances of a given resource that subject is allowed
       to read.
   2. A write scenario, in which authorization module should tell whether
       user has permission or not to perform such action.
"""
from typing import Dict, List, Tuple, Union

from kingdom.access.authorization.types import (
    TOKEN_ALL,
    AccessRequest,
    Permission,
    Policy,
    PolicyContext,
    Selector,
)


def check_read_permission(
    owned_policies: PolicyContext, access_request: AccessRequest
) -> List[Selector]:
    """
    Consider a subject that tries to access a resource. The access attempt is
    abstracted as AccessRequest and the whole set of policies it owns is
    represented as PolicyContext.

    This function returns the list of Selectors of requested resource that
    the subject is allowed to read.

    >>> access_request = AccessRequest(
        operation=Permission.READ, resource=Resource("Coupon"), selector="*"
    )
    >>> owned_perm = {
        "coupon": {
            "ab4c": (Permission.READ,),
            "bc3f": (Permission.READ, Permission.UPDATE),
        },
        "users": {
            "ccf3": (Permission.READ,),
            "abbc": (Permission.UPDATE, Permission.DELETE),
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

    # Subject has specific identifiers, we shall return them.
    allowed_ids = owned_policies[resource].keys()
    return list(allowed_ids)


def check_write_permission(
    owned_policies: PolicyContext,
    access_request: AccessRequest,
    transform_permission: bool = False,
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
            "ab4c": (Permission.READ,),
            "bc3f": (Permission.READ, Permission.UPDATE),
            "cc4a": (Permission.UPDATE,),
            "b4a3": (Permission.DELETE,),
        },
    }
    >>> check_write_permission(owned_perm, access_request)
    False

    More examples on test suite.
    """
    # Sanity check.
    assert access_request.operation & (
        Permission.CREATE | Permission.UPDATE | Permission.DELETE
    )

    resource = access_request.resource
    if resource not in owned_policies:
        # Resource is unknown to subject.
        return False
    # resource_owned = owned_policies[resource]

    # CREATE case is different than UPDATE and DELETE.
    # It requires a "*" selector.
    if access_request.operation == Permission.CREATE.value:
        # To CREATE, subject must have at least one '*' policy.
        if TOKEN_ALL not in owned_policies[resource]:
            return False

        # Checking is a simple O(1) step.
        return Permission.CREATE in owned_policies[resource][TOKEN_ALL]

    # Deal with UPDATE or DELETE
    # Check for generics.
    if TOKEN_ALL in owned_policies[resource]:
        permissions = owned_policies[resource][TOKEN_ALL]
        if is_allowed(permissions, access_request.operation):
            # Wildcard matches permission.
            return True
        # if access_request.operation in owned_resource[TOKEN_ALL]:
        #     return True

    # Then specify.
    if access_request.selector not in owned_policies[resource]:
        # No rule for requested instance. Denied.
        return False

    permissions = owned_policies[resource][access_request.selector]
    return is_allowed(permissions, access_request.operation)


def is_allowed(
    owned_permissions: Tuple[Permission, ...],
    requested_operation: Union[int, Permission],
) -> bool:
    """
    When a subject tries to perform a write, this function calculates whether
    the requested operation is allowed on a set of owned permissions.

    There are a few caveats:
     1. Write permission overrides read permission.
        e.g. If a Subject has any write permission, him/her implicitly
        have read permission.
     2. No write permissions override one-another.
        e.g. If a Subject has DELETE permission and it doesn't have
        UPDATE or CREATE permissions, it is only allowed to delete.


    >>> owned_perm = (Permission.READ, Permission.UPDATE, Permission.DELETE),
    >>> requested_op = Permission.CREATE
    >>> is_allowed(owned_perm, requested_op)
    False
    """

    if isinstance(requested_operation, int):
        requested_operation = Permission(requested_operation)

    # corner case is when requested permission is READ:
    if requested_operation == Permission.READ and owned_permissions:
        # if we have ANY permission, it means that the user is able to read
        return True

    permissions = 0
    for owned_permission in owned_permissions:
        permissions |= owned_permission

    return int(permissions & requested_operation) > 0
