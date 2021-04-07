# authorization.py
#
# Context: 
# When a user logs in, front-end receives a JWT on user's behalf.
# User has roles associated to him/her.
# And each of these roles have policies attached to them.
#
# USE CASE 1: Policy Packing and Unpacking 
# Whenever a user logs in, their policies gets packed into a JWT that's
# transferred within system's services boundaries.
#
# USE CASE 2: Policy Enforcement
# Whenever a user tries to perform an operation on a given resource
# i.e. an AccessRequest, it's up to authorization module to enforce
# whether user has enough privileges.

# USE CASE 1 -- In-depth
# Parse a list of Policy and return a mapping of resource-selector-operation
# This mapping should also *simplify* the policy and remove redundant policies

from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from typing import List

# Operation order:
# Split between READ and WRITE operations.
#   READ:  READ
#   WRITE: CREATE | UPDATE | DELETE
# 
# Rules:
#   1. WRITE permission overrides  READ permission.
#      e.g. If a USER have any of WRITE permission, him/her implicitly
#      have READ permission. 
#   2. No WRITE permissions override one-another.
#      e.g. If a user has DELETE permission and it doesn't have
#      UPDATE or CREATE permissions, it is only allowed to delete.


class Permission(Enum):
    READ = 0b000
    CREATE = 0b001
    UPDATE = 0b010
    DELETE = 0b100

    def __or__(self, other):
        if isinstance(other, Permission):
            other = other.value
        return self.value | other.value

    def __ror__(self, other):
        return self.__or__(other)

    def __and__(self, other):
        if isinstance(other, Permission):
            other = other.value
        return self.value & other.value


@dataclass
class Resource:
    name: str


@dataclass
class Policy(object):
    resource: Resource
    permissions: List[Permission]
    selectors: str


def test_tries_to_create_unauthorized():
    # user have no creation permissions
    input = [
        (Permission.READ),
        (Permission.READ, Permission.UPDATE),
        (Permission.READ, Permission.UPDATE, Permission.DELETE),
        (Permission.UPDATE, Permission.DELETE)
    ]
    for perm in input:
        assert has_permission(perm, Permission.CREATE) is False


def test_tries_to_update_anauthorized():
    # user have no update permission
    input = [
        (Permission.READ),
        (Permission.READ, Permission.CREATE),
        (Permission.READ, Permission.CREATE, Permission.DELETE),
        (Permission.CREATE, Permission.DELETE)
    ]
    for perm in input:
        assert has_permission(perm, Permission.UPDATE) is False


def test_tries_to_delete_anauthorized():
    # user have no delete permission
    input = [
        (Permission.READ),
        (Permission.READ, Permission.CREATE),
        (Permission.READ, Permission.CREATE, Permission.UPDATE),
        (Permission.CREATE, Permission.UPDATE)
    ]
    for perm in input:
        assert has_permission(perm, Permission.DELETE) is False


def test_tries_to_read_without_explicit_read_authorized():
    # user have only write permissions and tries to read
    input = [
        (Permission.CREATE),
        (Permission.UPDATE),
        (Permission.DELETE),
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
        assert has_permission((Permission.READ), perm) is False


def has_permission(
        owned_permissions: tuple,
        requested_operation: Permission
) -> bool:
    for permission in owned_permissions:
        permission |= permission

    return permission & requested_operation > 0


