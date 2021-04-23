from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import reduce
from typing import Dict, List, NamedTuple, Optional, Set, Tuple, Union

from kingdom.access import config
from kingdom.access.dsl import TOKEN_ALL
from kingdom.access.types import Payload, PolicyContext, SelectorPermissionMap


class Permission(Enum):
    """Fine-grained mapping of a permission operation."""

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
class Statement:
    """One and only one conditional statement"""

    identifier: str
    selector: str


@dataclass
class Policy:
    """
    An association of permissions that are allowed to be performed on
    on instances of a given resource that match ANY of the conditionals
    criteria"""

    resource: Resource
    permissions: Tuple[Permission, ...]
    conditionals: List[Statement]


@dataclass
class Role:
    name: str
    policies: List[Policy]

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class User:
    access_key: str
    roles: List[Optional[Role]]

    @property
    def policy_context(self) -> PolicyContext:
        "Builds a policy context reading all roles associated to a User"

        user_policies = list(self.resolve_policies())
        return encode_policies(user_policies)

    @property
    def jwt_payload(self) -> Payload:
        "Knows how to build a JWT Payload with necessary claims"

        expiration = datetime.utcnow() + timedelta(
            minutes=config.TOKEN_EXPIRATION_MIN
        )
        return dict(
            sub=self.access_key, exp=expiration, policies=self.encoded_policies
        )

    def resolve_policies(self):
        # TODO: Improve this typing
        for role in self.roles:
            for policy in role.policies:
                yield policy


PermissionTuple = Tuple[Permission, ...]
AnyPermission = Union[Permission, int]
PermissionTupleOrInt = Union[PermissionTuple, int]


def ptoi(permissions: PermissionTupleOrInt) -> int:
    """
    Considering that a permission can be both an integer and an instance of
    Permission, this function ensures that operations are done with a
    Permission type.
    It does by translating integer to Permission whenever needed.

    >>> ptoi(0)
    0
    >>> ptoi((Permission.CREATE, Permission.READ, Permission.UPDATE))
    3
    >>> ptoi((,))
    0
    """
    if isinstance(permissions, int):
        return permissions

    return (
        reduce(lambda a, b: a | b, permissions)
        if len(permissions) > 1
        else permissions[0].value
        if len(permissions) == 1
        else 0
    )


def union(
    permissions: PermissionTupleOrInt,
    incoming_permissions: PermissionTupleOrInt,
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
    return ptoi(permissions) | ptoi(incoming_permissions)


def build_redundant_context(policies: List[Policy]) -> PolicyContext:
    """
    Parses a list of Policy and return a mapping of
    resource per selector per permission, known as PolicyContext.

    Warning: This map is redundant i.e. "*" might have overlapping permissions
    with some other specific selectors. Take this example:

    >>> a_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE, Permission.CREATE,),
        conditionals=[Statement("resource.id", "*")]
    )
    >>> ya_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE,),
        conditionals=[Statement("resource.id", "5f34")]
    )
    >>> build_redundant_context([a_policy, ya_policy])
    {
        "account": {
            "*": 3,
            "5f34": 2,
        }
    }

    Note that "5f34" entry is redundant because "*" selector already
    contemplates this statement condition.
    """

    def pivot_policy(
        current_mapping: SelectorPermissionMap, policy: Policy
    ) -> SelectorPermissionMap:
        """Pivots a Policy into a map of Selector: PermissionInt
        It updates Permission value with context's permissions"""
        return {
            conditional.selector: union(
                permissions,
                current_mapping.get(conditional.selector, tuple()),
            )
            for conditional in policy.conditionals
        }

    context: PolicyContext = {}

    for policy in policies:
        # Aliasing:
        resource = policy.resource.alias
        permissions: PermissionTuple = policy.permissions
        if resource not in context:
            context[resource] = defaultdict(dict)

        context[resource].update(pivot_policy(context[resource], policy))

    return context


def remove_context_redundancy(context: PolicyContext) -> PolicyContext:
    """
    Given a redundant PolicyContext, remove any redundancy that might exist
    For now, redundancies origins from having to deal with "*" token.

    >>> a_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE, Permission.CREATE,),
        conditionals=[Statement("resource.id", "*")]
    )
    >>> ya_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE),
        conditionals=[Statement("resource.id", "5f34")]
    )
    >>> ctx = build_redundant_context([a_policy, ya_policy])
    >>> ctx
    {
        "account": {
            "*": 3,
            "5f34": 2,
        }
    }
    >>> remove_context_redundancy(ctx)
    {
        "account": {
            "*": 3,
        }
    }
    """
    simplified: PolicyContext = deepcopy(context)

    for resource, selector_perm in context.items():
        if TOKEN_ALL not in selector_perm:
            # Well, nothing to do then.
            continue

        for selector, permissions in selector_perm.items():
            # Subtract "*"'s permissions from the other permissions
            if selector == TOKEN_ALL:
                # Not this one.
                continue

            updated_perms: int = permissions & ~selector_perm[TOKEN_ALL]
            if updated_perms == 0:
                # All of this selector's permissions are already
                # contemplated by "*"
                del simplified[resource][selector]
            else:
                simplified[resource][selector] = updated_perms

    return simplified


def encode_policies(policies: List[Policy]) -> PolicyContext:
    """
    This functions parses a list of Policy and return a mapping of
    resource-selector-perimssion, known as PolicyContext.
    This mapping should also contain a simplification of redundant policies
    that a subject might have.

    >>> a_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE,),
        conditionals=[Statement("resource.id", "*")]
    )
    >>> ya_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ,),
        conditionals=[Statement("resource.id", "5f34")]
    )
    >>> pack_policies([a_policy, ya_policy])
    {
        "product": {
            "5f34": Permission.READ.value,
        },
        "account": {
            "*": Permission.UPDATE.value,
        },
    }

    # Which is the equivalent of:
    >>> pack_policies([a_policy, ya_policy])
    {
        "product": {
            "5f34": 0,
        },
        "account": {
            "*": 4,
        },
    }
    """
    context = build_redundant_context(policies)
    return remove_context_redundancy(context)
