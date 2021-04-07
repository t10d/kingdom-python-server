# authorization.py
#
# Context: 
# When a user logs in, front-end receives a JWT on user's behalf.
# User has roles associated to him/her.
# And each of these roles have policies attached to them.
#

from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

class Permission(Enum):
    READ = 0b000
    CREATE = 0b001
    UPDATE = 0b010
    DELETE = 0b100

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
    name: str


@dataclass
class Conditional:
    identifier: str
    selector: str


@dataclass
class Policy(object):
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
    product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.UPDATE,),
        conditionals=[
            Conditional("resource.id", "ab4f"),
            Conditional("resource.id", "13fa"),
        ]
    )

    ya_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.CREATE,),
        conditionals=[
            Conditional("resource.id", "*"),
        ]
    )

    account_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.READ,),
        conditionals=[
            Conditional("resource.id", "*"),
        ]
    )

    ya_account_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE,),
        conditionals=[
            Conditional("resource.id", "0bf3"),
            Conditional("resource.id", "bc0e"),
        ]
    )

    role_policies = [
        product_policy, ya_product_policy, account_policy, ya_account_policy
    ]

    owned_perm = {
        Resource("Product"): {
            "*": (Permission.READ,),
            "ab4f": (Permission.UPDATE, Permission.DELETE),
            "13fa": (Permission.UPDATE, Permission.DELETE),
        },
        Resource("Account"): {
            "*": (Permission.READ,),
            "0bf3": (Permission.UPDATE),
            "bc0e": (Permission.UPDATE),
        }
    }

    assert pack_policies(role_policies) == owned_perm


def pack_policies(policies: List[Policy]) -> Dict:
    owned = {}

    # iterative straightforward approach: on every iteration we keep on
    # building our output dictionary
    for policy in policies:
        if policy.resource not in owned:
            owned_permissions[resource] = dict()

        # iterate on every conditional
        for conditional in policy.conditionals:
            if conditional.selector not in owned[resource]:
                owned[resource] = policy.permissions
                # continue so code won't get too spaghetti
                continue

            # meaning that selector is already on owned_permissions[resource] 
            # we have to figure out first if it's a redundant permission
            existing_perm = set(owned[resource][conditional.selector])
            diff = existing_perm - set(policy.permissions)




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
#   2.1.   "*" in OwnedPermission.resource.selectors Or
#   2.2.   AccessRequest.resource.selector in OwnedPermission.resource.selectors
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
    input = [
        (Permission.READ,),
        (Permission.READ, Permission.UPDATE),
        (Permission.READ, Permission.UPDATE, Permission.DELETE),
        (Permission.UPDATE, Permission.DELETE)
    ]
    for perm in input:
        assert has_permission(perm, Permission.CREATE) is False


def test_tries_to_update_anauthorized():
    # user have no update permission
    input = [
        (Permission.READ,),
        (Permission.READ, Permission.CREATE),
        (Permission.READ, Permission.CREATE, Permission.DELETE),
        (Permission.CREATE, Permission.DELETE)
    ]
    for perm in input:
        assert has_permission(perm, Permission.UPDATE) is False


def test_tries_to_delete_anauthorized():
    # user have no delete permission
    input = [
        (Permission.READ,),
        (Permission.READ, Permission.CREATE),
        (Permission.READ, Permission.CREATE, Permission.UPDATE),
        (Permission.CREATE, Permission.UPDATE)
    ]
    for perm in input:
        assert has_permission(perm, Permission.DELETE) is False


def test_tries_to_read_without_explicit_read_authorized():
    # user have only write permissions and tries to read
    input = [
        (Permission.CREATE,),
        (Permission.UPDATE,),
        (Permission.DELETE,),
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
        assert has_permission((Permission.READ,), perm) is False


def has_permission(
        owned_permissions: tuple,
        requested_operation: Permission
) -> bool:
    # corner case is when requested permission is READ:
    if requested_operation == Permission.READ and len(owned_permissions) > 0:
        # if we have ANY permission, it means that the user is able to read
        return True

    for permission in owned_permissions:
        permission |= permission

    return permission & requested_operation > 0



