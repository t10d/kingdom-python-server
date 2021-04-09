# authorization.py
"""
 Context:
 When a user logs in, front-end receives a JWT on user's behalf.
 User has roles associated to him/her.
 And each of these roles have policies attached to them.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, NamedTuple, Tuple, Union

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


"""
USE CASE 1: Policy Packing
- Whenever a user logs in, their policies gets packed into a JWT that's
transferred within system's services boundaries.
- We don't need to unpack it, since it's a unidirectional step from
authorization service to JWTs. Incoming logic relies on unpacked data
structure

In-depth:
Parse a list of Policy and return a mapping of resource-selector-operation
This mapping should also *simplify* the policy and remove redundant policies
"""


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
                # Union
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
            # We now subtract "*"'s permissions from the other permissions
            if selector == TOKEN_ALL:
                # Not this one.
                continue
            current_perms = set(permissions)
            updated_perms = current_perms - all_token_perms

            if len(updated_perms) == 0:
                # Meaning that all of this selector's permissions are already
                # contemplated by "*"
                del owned[resource][selector]
            else:
                owned[resource][selector] = tuple(updated_perms)

    return owned


"""
USE CASE 2: Incoming AccessRequest
 Whenever a subject tries to perform an operation on a given resource
 i.e. an AccessRequest, it's up to authorization module to decide whether
 that operation is allowed.

 There are two authorization scenarios:
    1. A READ scenario, in which authorization module should pass-along to
        the server which instances that subject is allowed to read.
    2. A WRITE scenario, in which authorization module should tell whether
        user has permission or not.

 READ SCENARIO:
 Given that
  1. AccessRequest.operation is READ
  2. And AccessRequest.resource in OwnedPermission.resource
  3. Return OwnedPermission.resource.selectors keys.
    3.1. If "*" in OwnedPermission.resource.selectors, return only "*".

  PS: Since READ is the least privilege level, every key should hold at least
  enough privileges for read.
"""


@dataclass
class AccessRequest:
    operation: int
    resource: str
    selector: str

    def __init__(self, operation: Permission, resource: Resource,
                 selector: str):
        self.operation = operation.value
        self.resource = resource.alias
        self.selector = selector


def test_read_permission_filtering_unauthorized():
    access_request = AccessRequest(operation=Permission.READ,
                                   resource=Resource("Product"),
                                   selector="*")
    owned_perm = {
        "account": {
            "*": (Permission.CREATE, ),
        },
    }
    assert check_read_permission(owned_perm, access_request) == []

    access_request = AccessRequest(operation=Permission.READ,
                                   resource=Resource("Account"),
                                   selector="*")
    owned_perm = {
        "product": {
            "*": (Permission.READ, ),
        },
    }
    assert check_read_permission(owned_perm, access_request) == []


def test_read_permission_filtering_authorized_but_specific():
    access_request = AccessRequest(operation=Permission.READ,
                                   resource=Resource("Coupon"),
                                   selector="*")
    owned_perm = {
        "coupon": {
            "ab4c": (Permission.READ, ),
            "bc3f": (Permission.READ, Permission.UPDATE),
            "cc4a": (Permission.UPDATE, ),
            "b4a3": (Permission.DELETE, ),
        },
    }
    assert check_read_permission(
        owned_perm, access_request) == ["ab4c", "bc3f", "cc4a", "b4a3"]

    access_request = AccessRequest(operation=Permission.READ,
                                   resource=Resource("Coupon"),
                                   selector="*")
    owned_perm = {
        "coupon": {
            "*": (Permission.CREATE, ),
        },
    }
    assert check_read_permission(owned_perm, access_request) == ["*"]


def check_read_permission(owned_permissions: Dict,
                          access_request: AccessRequest) -> List:
    # Sanity check
    assert access_request.operation == Permission.READ.value

    if access_request.resource not in owned_permissions:
        # Subject has no permission related to requested resource.
        return []

    # Subject has at least one selector that it can read.
    if TOKEN_ALL in owned_permissions[access_request.resource]:
        # If it has any binding to "*", then it can read it all.
        return [TOKEN_ALL]

    # Subject has specific bindings, we shall return them.
    allowed_ids = owned_permissions[access_request.resource].keys()
    return list(allowed_ids)


"""
 WRITE SCENARIO:
 Given that
   1. AccessRequest.operation is CREATE|DELETE|UPDATE
   3. AccessRequest.resource in OwnedPermission.resource
   4. And that either
       2.1. "*" in OwnedPermission.resource.selectors Or
       2.2. AccessRequest.resource.selector in
            OwnedPermission.resource.selectors
   5. Check that
       AccessRequest.resource.selector.operation has permissions against
       OwnedPermission.resource.selector.operations

 PS: Note that in each of these steps, if a condition is not satisfied
 we instantly revoke.
"""


def test_write_permission_unauthorized():
    # Tries to write in an unknown resource to the subject
    access_request = AccessRequest(operation=Permission.CREATE,
                                   resource=Resource("User"),
                                   selector="*")
    owned_perm = {
        "product": {
            "*": (Permission.READ, ),
        },
    }
    assert check_write_permission(owned_perm, access_request) is False

    # Tries to write in a known resource but without enough privileges.
    access_request = AccessRequest(operation=Permission.CREATE,
                                   resource=Resource("Coupon"),
                                   selector="*")
    owned_perm = {
        "coupon": {
            "ab4c": (Permission.READ, ),
            "bc3f": (Permission.READ, Permission.UPDATE),
            "cc4a": (Permission.UPDATE, ),
            "b4a3": (Permission.DELETE, ),
        },
    }
    assert check_write_permission(owned_perm, access_request) is False

    # Tries to write in a known resource but without specific privileges
    access_request = AccessRequest(operation=Permission.UPDATE,
                                   resource=Resource("User"),
                                   selector="ffc0")
    owned_perm = {
        "user": {
            "*": (Permission.READ, Permission.CREATE),
            "abc3": (Permission.UPDATE, ),
        },
    }
    assert check_write_permission(owned_perm, access_request) is False

    # Tries to write in a known resource but without specific privileges
    access_request = AccessRequest(operation=Permission.DELETE,
                                   resource=Resource("User"),
                                   selector="c4fd")
    owned_perm = {
        "user": {
            "*": (Permission.READ, Permission.CREATE, Permission.UPDATE),
            "d3fc": (Permission.DELETE, ),
        },
    }
    assert check_write_permission(owned_perm, access_request) is False


def test_write_permission_authorized():
    # Tries to create a new item.
    access_request = AccessRequest(operation=Permission.CREATE,
                                   resource=Resource("User"),
                                   selector="*")
    owned_perm = {
        "user": {
            "*": (
                Permission.UPDATE,
                Permission.CREATE,
            ),
        },
    }
    assert check_write_permission(owned_perm, access_request) is True

    # Tries to update a specific value on a wildcard policy.
    access_request = AccessRequest(operation=Permission.UPDATE,
                                   resource=Resource("Coupon"),
                                   selector="43df")
    owned_perm = {
        "coupon": {
            "*": (Permission.READ, Permission.UPDATE, Permission.DELETE),
        },
    }
    assert check_write_permission(owned_perm, access_request) is True

    # Tries to delete a specific value on a specific policy.
    access_request = AccessRequest(operation=Permission.DELETE,
                                   resource=Resource("User"),
                                   selector="3dc4")
    owned_perm = {
        "user": {
            "*": (Permission.CREATE, ),
            "3dc4": (Permission.DELETE, ),
        },
    }
    assert check_write_permission(owned_perm, access_request) is True


def check_write_permission(owned_permissions: Dict,
                           access_request: AccessRequest) -> bool:
    # Sanity check.
    assert (access_request.operation \
             & (Permission.CREATE | Permission.UPDATE | Permission.DELETE))

    if access_request.resource not in owned_permissions:
        # Resource is unknown to subject.
        return False

    owned_resource = owned_permissions[access_request.resource]
    # CREATE case is different than UPDATE and DELETE.
    # Because it requires a "*" selector.
    if access_request.operation == Permission.CREATE.value:
        # To CREATE, subject must have at least one '*' policy.
        if TOKEN_ALL not in owned_resource:
            return False

        # Checking is a simple O(1) step.
        return Permission.CREATE in owned_resource[TOKEN_ALL]

    # Deal with UPDATE or DELETE
    # Check for generics.
    if TOKEN_ALL in owned_resource:
        if is_allowed(owned_resource[TOKEN_ALL], access_request.operation):
            # Wildcard matches permission.
            return True
        # if access_request.operation in owned_resource[TOKEN_ALL]:
        #     return True

    # Then specify.
    if access_request.selector not in owned_resource:
        # No rule for requested instance. Denied.
        return False

    return is_allowed(owned_resource[access_request.selector],
                      access_request.operation)
    # return access_request.operation in owned_resource[access_request.selector]


"""
USE CASE 3: Permission check
Given that an incoming AccessRequest is dispatched and a common selector
exist in both OwnedPermission and AccessRequest, it's up to this logic
to return whether those permissions results in an Allow statement.

 Operation order:
 Split between READ and WRITE operations.
   READ:  READ
   WRITE: CREATE | UPDATE | DELETE

 Rules:
   1. WRITE permission overrides  READ permission.
      e.g. If a Subject has any of WRITE permission, him/her implicitly
      have READ permission.
   2. No WRITE permissions override one-another.
      e.g. If a Subject has DELETE permission and it doesn't have
      UPDATE or CREATE permissions, it is only allowed to delete.
"""


def test_tries_to_create_unauthorized():
    # user have no creation permissions
    input = [(Permission.READ, ), (Permission.READ, Permission.UPDATE),
             (Permission.READ, Permission.UPDATE, Permission.DELETE),
             (Permission.UPDATE, Permission.DELETE)]
    for perm in input:
        assert is_allowed(perm, Permission.CREATE) is False


def test_tries_to_update_anauthorized():
    # user have no update permission
    input = [(Permission.READ, ), (Permission.READ, Permission.CREATE),
             (Permission.READ, Permission.CREATE, Permission.DELETE),
             (Permission.CREATE, Permission.DELETE)]
    for perm in input:
        assert is_allowed(perm, Permission.UPDATE) is False


def test_tries_to_delete_anauthorized():
    # user have no delete permission
    input = [(Permission.READ, ), (Permission.READ, Permission.CREATE),
             (Permission.READ, Permission.CREATE, Permission.UPDATE),
             (Permission.CREATE, Permission.UPDATE)]
    for perm in input:
        assert is_allowed(perm, Permission.DELETE) is False


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
        assert is_allowed(perm, Permission.READ)


def test_tries_to_write_but_has_only_read():
    # user have only read permissions and tries to do all writes
    input = [
        Permission.CREATE,
        Permission.UPDATE,
        Permission.DELETE,
    ]
    for perm in input:
        assert is_allowed((Permission.READ, ), perm) is False


def is_allowed(owned_permissions: tuple,
               requested_operation: Union[int, Permission]) -> bool:
    if isinstance(requested_operation, int):
        requested_operation = Permission(requested_operation)

    # corner case is when requested permission is READ:
    if requested_operation == Permission.READ and len(owned_permissions) > 0:
        # if we have ANY permission, it means that the user is able to read
        return True

    permissions = 0
    for owned_permission in owned_permissions:
        permissions |= owned_permission

    return (permissions & requested_operation) > 0
