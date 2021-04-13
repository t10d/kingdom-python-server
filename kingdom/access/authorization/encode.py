"""
encode.py

Whenever a user is successfully authenticated, application should be able to
properly encode its policies in an associative mapping form to be packed within
JWT payload.
"""

from functools import reduce
from typing import Dict, List, Optional, Tuple, Union

from kingdom.access.authorization.types import (
    TOKEN_ALL,
    Conditional,
    Permission,
    Policy,
    PolicyContext,
    PolicyContextRaw,
    Resource,
    Selector,
)

PermissionTuple = Tuple[Permission, ...]


def itop(permissions: Union[int, PermissionTuple]) -> PermissionTuple:
    """
    Considering that a permission can be both an integer and an instance of
    Permission, this function ensures that operations are done with a
    Permission type.
    It does by translating integer to Permission whenever needed.

    >>> atoi_permission(0)
    (Permission.READ,)
    >>> atoi_permission((Permission.CREATE, Permission.READ))
    (Permission.CREATE, Permission.READ)
    """
    if isinstance(permissions, int):
        return (Permission(permissions),)
    return permissions


def union_permissions(
    permissions: Union[PermissionTuple, int],
    incoming_permissions: Union[PermissionTuple, int],
) -> int:
    """
    Given a set of permissions and a set of incoming permissions that should
    be unionized, this method adds them up.

    >>> union_permissions((Permission.READ,), 2)
    3
    >>> union_permissions(
        (Permission.DELETE,), (Permission.CREATE, Permission.UPDATE))
    7
    >>> union_permissions((Permission.CREATE,), (Permission.CREATE,))
    1
    """
    current: PermissionTuple = itop(permissions)
    incoming: PermissionTuple = itop(incoming_permissions)

    updated = set(current) | set(incoming)
    perms = reduce(lambda a, b: a | b, updated)

    if isinstance(perms, Permission):
        # If updated has only one element, reduce will output the element
        # itself. Hence we need to get its value
        return perms.value
    return perms


def encode(policies: List[Policy]) -> PolicyContext:
    """
    This functions parses a list of Policy and return a mapping of
    resource-selector-perimssion, known as PolicyContext.
    This mapping should also contain a simplification of redundant policies
    that a subject might have.

    >>> a_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE,),
        conditionals=[Conditional("resource.id", "*")]
    )
    >>> ya_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ,),
        conditionals=[Conditional("resource.id", "5f34")]
    )
    >>> pack_policies([a_policy, ya_policy])
    {
        "product": {
            "5f34": (Permission.READ,)
        },
        "account": {
            "*": (Permission.UPDATE,)
        }
    }

    >>> pack_policies([a_policy, ya_policy])
    {
        "product": {
            "5f34": 1
        },
        "account": {
            "*": 4
        }
    }

    TODO: This is currently a side-effectful implementation, we could def.
    implement a pure one.
    """
    # owned: PolicyContext = {}
    owned: PolicyContextRaw = {}

    # Iterative approach: on every iteration we keep on
    # building output dictionary
    for policy in policies:
        resource = policy.resource.alias
        permissions = policy.permissions
        if resource not in owned:
            owned[resource] = {}

        # Iterate on every conditional
        for conditional in policy.conditionals:
            selector = conditional.selector
            # There are two kinds of selectors: specific and generics.
            # And a selector already exist for a given resource or it doesn't.
            if selector in owned[resource]:
                existing_permissions = owned[resource][selector]
            else:
                existing_permissions = tuple()

            owned[resource][selector] = union_permissions(
                permissions, existing_permissions
            )

    # Now remove any redundant permission due to a possible "*" selector
    # Brute-force.
    for resource, selector_perm in owned.items():
        if TOKEN_ALL not in selector_perm:
            # Well, nothing to do then.
            continue

        # all_token_perms = set(selector_perm[TOKEN_ALL])
        for selector, permissions in selector_perm.items():
            # Subtract "*"'s permissions from the other permissions
            if selector == TOKEN_ALL:
                # Not this one.
                continue

            updated_perms = permissions & ~selector_perm[TOKEN_ALL]
            if updated_perms == 0:
                # All of this selector's permissions are already
                # contemplated by "*"
                del owned[resource][selector]
            else:
                owned[resource][selector] = updated_perms

    return owned
