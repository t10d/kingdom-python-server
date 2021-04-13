from kingdom.access.authorization.model import (
    AccessRequest,
    Permission,
    Policy,
    Resource,
)
from kingdom.access.authorization.verify import (
    check_read_permission,
    check_write_permission,
    is_allowed,
)

# Test read scenario, check_read_permission


def test_read_permission_filtering_unauthorized():
    access_request = AccessRequest(
        operation=Permission.READ, resource=Resource("Product"), selector="*"
    )
    owned_perm = {
        "account": {"*": (Permission.CREATE,), },
    }
    assert check_read_permission(owned_perm, access_request) == []

    access_request = AccessRequest(
        operation=Permission.READ, resource=Resource("Account"), selector="*"
    )
    owned_perm = {
        "product": {"*": (Permission.READ,), },
    }
    assert check_read_permission(owned_perm, access_request) == []


def test_read_permission_filtering_authorized_but_specific():
    access_request = AccessRequest(
        operation=Permission.READ, resource=Resource("Coupon"), selector="*"
    )
    owned_perm = {
        "coupon": {
            "ab4c": (Permission.READ,),
            "bc3f": (Permission.READ, Permission.UPDATE),
            "cc4a": (Permission.UPDATE,),
            "b4a3": (Permission.DELETE,),
        },
    }
    assert check_read_permission(owned_perm, access_request) == [
        "ab4c",
        "bc3f",
        "cc4a",
        "b4a3",
    ]

    access_request = AccessRequest(
        operation=Permission.READ, resource=Resource("Coupon"), selector="*"
    )
    owned_perm = {
        "coupon": {"*": (Permission.CREATE,), },
    }
    assert check_read_permission(owned_perm, access_request) == ["*"]


# Test write scenario, check_write_permission


def test_write_permission_unauthorized():
    # Tries to write in an unknown resource to the subject
    access_request = AccessRequest(
        operation=Permission.CREATE, resource=Resource("User"), selector="*"
    )
    owned_perm = {
        "product": {"*": (Permission.READ,), },
    }
    assert check_write_permission(owned_perm, access_request) is False

    # Tries to write in a known resource but without enough privileges.
    access_request = AccessRequest(
        operation=Permission.CREATE, resource=Resource("Coupon"), selector="*"
    )
    owned_perm = {
        "coupon": {
            "ab4c": (Permission.READ,),
            "bc3f": (Permission.READ, Permission.UPDATE),
            "cc4a": (Permission.UPDATE,),
            "b4a3": (Permission.DELETE,),
        },
    }
    assert check_write_permission(owned_perm, access_request) is False

    # Tries to write in a known resource but without specific privileges
    access_request = AccessRequest(
        operation=Permission.UPDATE, resource=Resource("User"), selector="ffc0"
    )
    owned_perm = {
        "user": {
            "*": (Permission.READ, Permission.CREATE),
            "abc3": (Permission.UPDATE,),
        },
    }
    assert check_write_permission(owned_perm, access_request) is False

    # Tries to write in a known resource but without specific privileges
    access_request = AccessRequest(
        operation=Permission.DELETE, resource=Resource("User"), selector="c4fd"
    )
    owned_perm = {
        "user": {
            "*": (Permission.READ, Permission.CREATE, Permission.UPDATE),
            "d3fc": (Permission.DELETE,),
        },
    }
    assert check_write_permission(owned_perm, access_request) is False


def test_write_permission_authorized():
    # Tries to create a new item.
    access_request = AccessRequest(
        operation=Permission.CREATE, resource=Resource("User"), selector="*"
    )
    owned_perm = {
        "user": {"*": (Permission.UPDATE, Permission.CREATE,), },
    }
    assert check_write_permission(owned_perm, access_request) is True

    # Tries to update a specific value on a wildcard policy.
    access_request = AccessRequest(
        operation=Permission.UPDATE, resource=Resource("Coupon"), selector="43df"
    )
    owned_perm = {
        "coupon": {"*": (Permission.READ, Permission.UPDATE, Permission.DELETE), },
    }
    assert check_write_permission(owned_perm, access_request) is True

    # Tries to delete a specific value on a specific policy.
    access_request = AccessRequest(
        operation=Permission.DELETE, resource=Resource("User"), selector="3dc4"
    )
    owned_perm = {
        "user": {"*": (Permission.CREATE,), "3dc4": (Permission.DELETE,), },
    }
    assert check_write_permission(owned_perm, access_request) is True


# Test is_allowed()


def test_tries_to_create_unauthorized():
    # user have no creation permissions
    input = [
        (Permission.READ,),
        (Permission.READ, Permission.UPDATE),
        (Permission.READ, Permission.UPDATE, Permission.DELETE),
        (Permission.UPDATE, Permission.DELETE),
    ]
    for perm in input:
        assert is_allowed(perm, Permission.CREATE) is False


def test_tries_to_update_anauthorized():
    # user have no update permission
    input = [
        (Permission.READ,),
        (Permission.READ, Permission.CREATE),
        (Permission.READ, Permission.CREATE, Permission.DELETE),
        (Permission.CREATE, Permission.DELETE),
    ]
    for perm in input:
        assert is_allowed(perm, Permission.UPDATE) is False


def test_tries_to_delete_anauthorized():
    # user have no delete permission
    input = [
        (Permission.READ,),
        (Permission.READ, Permission.CREATE),
        (Permission.READ, Permission.CREATE, Permission.UPDATE),
        (Permission.CREATE, Permission.UPDATE),
    ]
    for perm in input:
        assert is_allowed(perm, Permission.DELETE) is False


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
        assert is_allowed(perm, Permission.READ)


def test_tries_to_write_but_has_only_read():
    # user have only read permissions and tries to do all writes
    input = [
        Permission.CREATE,
        Permission.UPDATE,
        Permission.DELETE,
    ]
    for perm in input:
        assert is_allowed((Permission.READ,), perm) is False
