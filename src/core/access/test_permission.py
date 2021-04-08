# authorization.py
"""
 Context:
 When a user logs in, front-end receives a JWT on user's behalf.
 User has roles associated to him/her.
 And each of these roles have policies attached to them.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

TOKEN_ALL = "*"


class Permission(Enum):
    """Operation-permission"""
    READ = 0b000
    CREATE = 0b001
    UPDATE = 0b010
    DELETE = 0b100

    def __hash__(self) -> int:
        return hash(self.value)

    def __or__(self, other):
        if isinstance(other, Permission):
            other = other.value
        return self.value | other

    def __ror__(self, other):
        return self.__or__(other)

    def __and__(self, other):
        if isinstance(other, Permission):
            other = other.value
        return self.value & other

    def __rand__(self, other):
        return self.__and__(other)


@dataclass
class Resource:
    """An enterprise-wide resource wrapper"""
    name: str

    def __init__(self, name: str):
        self.name = name
        self.alias = name.lower()


@dataclass
class Conditional:
    """One and only one conditional clause"""
    identifier: str
    selector: str


@dataclass
class Policy:
    """An association of permissions that are allowed to be performed on
    on instances of a given resource that match ANY of the conditionals
    criteria"""
    resource: Resource
    permissions: Tuple[Permission]
    conditionals: List[Conditional]


# USE CASE 1: Policy Packing and Unpacking
# Whenever a user logs in, their policies gets packed into a JWT that's
# transferred within system's services boundaries.
#
# In-depth:
# Parse a list of Policy and return a mapping of resource-selector-operation
# This mapping should also *simplify* the policy and remove redundant policies


def test_simple_policy_packing():
    """Given a list of Policies with no overlapping conditional selectors,
    we expect a well-formatted DTO dict"""
    product_policy = Policy(resource=Resource("Product"),
                            permissions=(Permission.UPDATE, ),
                            conditionals=[
                                Conditional("resource.id", "ab4f"),
                                Conditional("resource.id", "13fa"),
                            ])

    ya_product_policy = Policy(resource=Resource("Product"),
                               permissions=(Permission.CREATE, ),
                               conditionals=[
                                   Conditional("resource.id", "*"),
                               ])

    account_policy = Policy(resource=Resource("Account"),
                            permissions=(Permission.READ, ),
                            conditionals=[
                                Conditional("resource.id", "*"),
                            ])

    ya_account_policy = Policy(resource=Resource("Account"),
                               permissions=(Permission.UPDATE, ),
                               conditionals=[
                                   Conditional("resource.id", "0bf3"),
                                   Conditional("resource.id", "bc0e"),
                               ])

    role_policies = [
        product_policy, ya_product_policy, account_policy, ya_account_policy
    ]

    owned_perm = {
        "product": {
            "*": (Permission.CREATE, ),
            "ab4f": (Permission.UPDATE, ),
            "13fa": (Permission.UPDATE, ),
        },
        "account": {
            "*": (Permission.READ, ),
            "0bf3": (Permission.UPDATE, ),
            "bc0e": (Permission.UPDATE, ),
        }
    }

    assert pack_policies(role_policies) == owned_perm


def test_redundant_policy_packing():
    """Given a list of Policies with overlapping conditional selectors,
    we expect a well-formatted DTO dict"""
    product_policy = Policy(resource=Resource("Product"),
                            permissions=(Permission.READ, Permission.CREATE),
                            conditionals=[
                                Conditional("resource.id", "*"),
                            ])

    ya_product_policy = Policy(resource=Resource("Product"),
                               permissions=(Permission.READ,
                                            Permission.UPDATE),
                               conditionals=[
                                   Conditional("resource.id", "7fb4"),
                                   Conditional("resource.id", "49f3"),
                                   Conditional("resource.id", "abc9"),
                               ])

    yao_product_policy = Policy(resource=Resource("Product"),
                                permissions=(
                                    Permission.READ,
                                    Permission.DELETE,
                                ),
                                conditionals=[
                                    Conditional("resource.id", "aaa"),
                                    Conditional("resource.id", "abc9"),
                                ])

    role_policies = [
        product_policy,
        ya_product_policy,
        yao_product_policy,
    ]

    owned_perm = {
        "product": {
            "*": (
                Permission.READ,
                Permission.CREATE,
            ),
            "7fb4": (Permission.UPDATE, ),
            "49f3": (Permission.UPDATE, ),
            "abc9": (Permission.UPDATE, Permission.DELETE),
            "aaa": (Permission.DELETE, ),
        },
    }

    assert pack_policies(role_policies) == owned_perm


def pack_policies(policies: List[Policy]) -> Dict:
    """
    Pack a list of policies into a known PolicyDTO format.
    TODO: Refactor this in order to properly encapsulate output DTO format.

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
    """
    owned: Dict[str, Dict[str, tuple]] = {}

    # iterative straightforward approach: on every iteration we keep on
    # building our output dictionary
    for policy in policies:
        resource = policy.resource.alias
        permissions = policy.permissions
        if resource not in owned:
            owned[resource] = {}

        # iterate on every conditional
        for conditional in policy.conditionals:
            selector = conditional.selector
            # There are two kinds of selectors: specific and generics.
            # And a selector already exist for a given resource or it doesn't.
            if selector in owned[resource]:
                # When a selector already exists, we make sure we keep
                # permissions unique
                current_perms = set(owned[resource][selector])
                incoming_perms = set(permissions)
                updated_permissions = tuple(incoming_perms | current_perms)
                owned[resource][selector] = updated_permissions
            else:
                # Otherwise, it's a new selector, hence a new entry on
                # dict.
                owned[resource][selector] = tuple(permissions)

    # Brute-forcing, we now iterate over each resource and remove
    # redundant permissions
    for resource, selector_dict in owned.items():
        if TOKEN_ALL not in selector_dict:
            # nothing to do
            continue

        all_token_perms = set(selector_dict[TOKEN_ALL])
        for selector, permissions in selector_dict.items():
            # We now subtract "*" from all of the other permissions
            if selector == TOKEN_ALL:
                # Not this one.
                continue
            current_perms = set(permissions)
            updated_perms = current_perms - all_token_perms

            if len(updated_perms) == 0:
                # Meaning that all of this selector permissions are already
                # contemplated by "*"
                del owned[resource][selector]
            else:
                owned[resource][selector] = tuple(updated_perms)

    return owned


# USE CASE 2: Policy Enforcement
# Whenever a user tries to perform an operation on a given resource
# i.e. an AccessRequest, it's up to authorization module to enforce
# whether user has enough privileges.
# Scenario:
#  1. Subject has a map of OwnedPermission
#  2. Subject emits a AccessRequest
#
# Given that
#   1. AccessRequest.resource in OwnedPermission.resource
#   2. And that either
#       2.1. "*" in OwnedPermission.resource.selectors Or
#       2.2. AccessRequest.resource.selector in
#            OwnedPermission.resource.selectors
#   3. We must check that
#       AccessRequest.resource.selector.operation has permissions against
#       OwnedPermission.resource.selector.operations
#
# Operation order:
# Split between READ and WRITE operations.
#   READ:  READ
#   WRITE: CREATE | UPDATE | DELETE
#
# Rules:
#   1. WRITE permission overrides  READ permission.
#      e.g. If a Subject has any of WRITE permission, him/her implicitly
#      have READ permission.
#   2. No WRITE permissions override one-another.
#      e.g. If a Subject has DELETE permission and it doesn't have
#      UPDATE or CREATE permissions, it is only allowed to delete.


def test_tries_to_create_unauthorized():
    # user have no creation permissions
    input = [(Permission.READ, ), (Permission.READ, Permission.UPDATE),
             (Permission.READ, Permission.UPDATE, Permission.DELETE),
             (Permission.UPDATE, Permission.DELETE)]
    for perm in input:
        assert has_permission(perm, Permission.CREATE) is False


def test_tries_to_update_anauthorized():
    # user have no update permission
    input = [(Permission.READ, ), (Permission.READ, Permission.CREATE),
             (Permission.READ, Permission.CREATE, Permission.DELETE),
             (Permission.CREATE, Permission.DELETE)]
    for perm in input:
        assert has_permission(perm, Permission.UPDATE) is False


def test_tries_to_delete_anauthorized():
    # user have no delete permission
    input = [(Permission.READ, ), (Permission.READ, Permission.CREATE),
             (Permission.READ, Permission.CREATE, Permission.UPDATE),
             (Permission.CREATE, Permission.UPDATE)]
    for perm in input:
        assert has_permission(perm, Permission.DELETE) is False


def test_tries_to_read_without_explicit_read_authorized():
    # user have only write permissions and tries to read
    input = [
        (Permission.CREATE, ),
        (Permission.UPDATE, ),
        (Permission.DELETE, ),
        (Permission.CREATE, Permission.DELETE),
        (Permission.CREATE, Permission.UPDATE),
        (Permission.DELETE, Permission.UPDATE),
        (Permission.CREATE, Permission.DELETE, Permission.UPDATE),
    ]
    for perm in input:
        assert has_permission(perm, Permission.READ)


def test_tries_to_write_but_has_only_read():
    # user have only read permissions and tries to do all writes
    input = [
        Permission.CREATE,
        Permission.UPDATE,
        Permission.DELETE,
    ]
    for perm in input:
        assert has_permission((Permission.READ, ), perm) is False


def has_permission(owned_permissions: tuple,
                   requested_operation: Permission) -> bool:
    # corner case is when requested permission is READ:
    if requested_operation == Permission.READ and len(owned_permissions) > 0:
        # if we have ANY permission, it means that the user is able to read
        return True

    permissions = 0
    for owned_permission in owned_permissions:
        permissions |= owned_permission

    return (permissions & requested_operation) > 0
