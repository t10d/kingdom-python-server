"""
encode.py

Whenever a user is successfully authenticated, application should be able to
properly encode its policies in an associative mapping form to be packed within
JWT payload.
"""

from typing import Dict, List, Tuple

from kingdom.access.authorization.model import (
    TOKEN_ALL,
    Conditional,
    Permission,
    Policy,
    PolicyContext,
    Resource,
    Selector,
)


def unique_permissions(
    current_permissions: Tuple[Permission, ...],
    incoming_permissions: Tuple[Permission, ...],
) -> Tuple[Permission, ...]:
    current = set(current_permissions)
    incoming = set(incoming_permissions)
    # Union
    return tuple(current | incoming)


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

    TODO: This is currently a side-effectful implementation, we could def.
    implement a pure one.
    """
    owned: PolicyContext = {}

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
                # When a selector already exists, we make sure we keep
                # permissions unique
                owned[resource][selector] = unique_permissions(
                    owned[resource][selector], permissions
                )
            else:
                # Otherwise, it's a new selector, hence a new entry
                owned[resource][selector] = tuple(permissions)

    # Now remove any redundant permission due to a possible "*" selector
    # Brute-force.
    for resource, selector_perm in owned.items():
        if TOKEN_ALL not in selector_perm:
            # Well, nothing to do then.
            continue

        all_token_perms = set(selector_perm[TOKEN_ALL])
        for selector, permissions in selector_perm.items():
            # Subtract "*"'s permissions from the other permissions
            if selector == TOKEN_ALL:
                # Not this one.
                continue
            current_perms = set(permissions)
            updated_perms = current_perms - all_token_perms

            if not updated_perms:
                # All of this selector's permissions are already
                # contemplated by "*"
                del owned[resource][selector]
            else:
                owned[resource][selector] = tuple(updated_perms)

    return owned
