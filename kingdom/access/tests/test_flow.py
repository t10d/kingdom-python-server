from typing import List, Tuple

from kingdom.access.base import Permission, Policy, Resource
from kingdom.access.flow import (
    AccessRequest,
    NotEnoughPrivilegesErr,
    authorize,
    check_permission,
    get_read_scope,
    is_write_allowed,
)
from kingdom.access.types import PolicyContext
from pytest import raises

CREATE = Permission.CREATE | 0
READ = Permission.READ | 0
UPDATE = Permission.UPDATE | 0
DELETE = Permission.DELETE | 0


class TestAuthorize:
    fn = authorize

    def test_user_tries_to_read_everything(self):
        user_policies: PolicyContext = {
            "user": {"00df": READ | UPDATE},
            "product": {"*": READ},
        }
        # Purposefully don't pass a selector, meaning it's trying to read
        # everything. But user can't see anything from coupons.
        with raises(NotEnoughPrivilegesErr):
            _ = authorize(user_policies, resource="coupon", operation="READ")

        scope = authorize(user_policies, resource="user", operation="READ")
        assert scope == ["00df"]

        scope = authorize(user_policies, resource="product", operation="READ")
        assert scope == ["*"]

    def test_user_tries_to_read_specifics(self):
        user_policies: PolicyContext = {
            "coupon": {"00df": READ, "ddf9": READ, "ddfc": READ, "fcc3": READ},
        }

        with raises(NotEnoughPrivilegesErr):
            scope = authorize(
                user_policies,
                resource="coupon",
                operation="READ",
                selector="d3f4",
            )

        scope = authorize(
            user_policies, resource="coupon", operation="READ", selector="fcc3"
        )
        assert scope == ["fcc3"]

    def test_user_tries_to_write_on_specific_policies(self):
        user_id = "00df"
        user_policies: PolicyContext = {
            "user": {user_id: READ | UPDATE},
            "product": {"*": READ},
        }
        with raises(NotEnoughPrivilegesErr):
            _ = authorize(user_policies, resource="user", operation="CREATE")

        with raises(NotEnoughPrivilegesErr):
            # This should fail because this attempt is to update all users,
            # there is an implicit selector
            _ = authorize(user_policies, resource="user", operation="UPDATE")

        with raises(NotEnoughPrivilegesErr):
            # Tries to update or delete another user than itself.
            _ = authorize(
                user_policies,
                resource="user",
                operation="DELETE",
                selector="0f0f",
            )

        scope = authorize(
            user_policies,
            resource="user",
            operation="UPDATE",
            selector=user_id,
        )
        assert scope == [user_id]

    def test_user_tries_to_write_on_generic_policies(self):
        supervisor_id = "3fd0"
        # Read operations are redundant but explicit is always better than
        # implicit.
        sup_policies: PolicyContext = {
            "user": {"*": READ},
            "product": {"*": READ | CREATE | UPDATE},
            "group": {"*": READ | CREATE},
            "role": {
                "3043": READ | UPDATE,
                "34cd": READ | UPDATE,
                "0039": READ | UPDATE,
                "ccdf": READ | UPDATE,
            },
        }

        # This supervisor can only create products and groups. Let's make sure:
        with raises(NotEnoughPrivilegesErr):
            _ = authorize(sup_policies, resource="user", operation="CREATE")

        with raises(NotEnoughPrivilegesErr):
            _ = authorize(sup_policies, resource="role", operation="CREATE")

        scope = authorize(sup_policies, resource="product", operation="CREATE")
        assert scope == ["*"]

        # Is not allowed to delete any role as well
        with raises(NotEnoughPrivilegesErr):
            _ = authorize(
                sup_policies,
                resource="role",
                operation="DELETE",
                selector="3043",
            )

        # But finally, it can update its subordinate's roles
        scope = authorize(
            sup_policies, resource="role", operation="UPDATE", selector="3043"
        )
        assert scope == ["3043"]


class TestReadPermission:
    "Test permissions on a read scenario"
    fn = get_read_scope

    def test_read_products_with_zero_policies(self):
        "User tries to read products but has no permission to read them"
        access_request = AccessRequest(
            operation="READ", resource="product", selector="*",
        )
        owned_perm: PolicyContext = {}
        assert get_read_scope(owned_perm, access_request) == []

    def test_read_products_with_ticket_create_policy(self):
        "User tries to read products but has only permission to create tickets"
        access_request = AccessRequest(
            operation="READ", resource="product", selector="*",
        )
        owned_perm = {
            "ticket": {"*": READ | CREATE, },
        }
        assert get_read_scope(owned_perm, access_request) == []

    def test_read_coupons_with_specific_cupons_policy(self):
        "User tries to read all coupons but can only see selected ones."
        access_request = AccessRequest(
            operation="READ", resource="coupon", selector="*",
        )
        owned_perm: PolicyContext = {
            "coupon": {
                "ab4c": READ,
                "bc3f": READ | UPDATE,
                "cc4a": UPDATE,
                "b4a3": DELETE,
            },
        }
        assert get_read_scope(owned_perm, access_request) == [
            "ab4c",
            "bc3f",
            "cc4a",
            "b4a3",
        ]

    def test_read_coupons_with_write_all_coupons_policy(self):
        "User tries to read all coupons and user is allowed to manage them"
        access_request = AccessRequest(
            operation="READ", resource="coupon", selector="*",
        )
        owned_perm = {
            "coupon": {"*": CREATE | UPDATE | DELETE, },
        }
        assert get_read_scope(owned_perm, access_request) == ["*"]

    def test_read_accounts_with_self_edit_policy(self):
        "User tries to read all coupons but has permissions to read only one"
        access_request = AccessRequest(
            operation="READ", resource="account", selector="*",
        )
        owned_perm = {
            "coupon": {"bcc3": READ, },
            "account": {"ddf3": UPDATE},
            "product": {"*": READ},
            "ticket": {"*": CREATE},
        }
        assert get_read_scope(owned_perm, access_request) == [
            "ddf3",
        ]


class TestVerifyWritePermissions:
    "Test permissions on a write scenario"
    fn = is_write_allowed

    def test_rules_without_policies(self):
        "User tries to write a rule without any policies"
        create_rule = AccessRequest(
            operation="CREATE", resource="rule", selector="*",
        )
        owned_perm: PolicyContext = {}
        assert is_write_allowed(owned_perm, create_rule) is False

    def test_create_user_with_product_read_policy(self):
        "User tries to create a user but has basic read policies"
        create_user = AccessRequest(
            operation="CREATE", resource="user", selector="*",
        )
        owned_perm = {
            "product": {"*": READ, },
            "user": {"*": READ | UPDATE | DELETE, },
            "coupons": {"33f0": READ, "ddf0": READ},
        }
        assert is_write_allowed(owned_perm, create_user) is False

        create_product = AccessRequest(
            operation="CREATE", resource="product", selector="*",
        )
        assert is_write_allowed(owned_perm, create_product) is False

    def test_create_coupon_without_create_all_policy(self):
        "User tries to create a coupon but can only manage a few of them"
        create_coupon = AccessRequest(
            operation="CREATE", resource="coupon", selector="*",
        )
        owned_perm = {
            "coupon": {
                "ab4c": READ,
                "bc3f": READ | UPDATE,
                "cc4a": READ | UPDATE,
                "b4a3": READ | DELETE,
            },
        }
        assert is_write_allowed(owned_perm, create_coupon) is False

        update_coupon = AccessRequest(
            operation="UPDATE", resource="coupon", selector="ab4c"
        )

        assert is_write_allowed(owned_perm, update_coupon) is False

    def test_delete_user_without_enough_policies(self):
        "User tries to delete user without specific policy"
        delete_user = AccessRequest(
            operation="DELETE", resource="user", selector="ffc0",
        )
        owned_perm = {
            "coupon": {"*": READ | CREATE | UPDATE | DELETE},
            "user": {"*": READ | CREATE, "abc3": UPDATE, },
        }
        assert is_write_allowed(owned_perm, delete_user) is False

    def test_create_user_with_proper_policy(self):
        "User tries to create a new user"
        create_user = AccessRequest(
            operation="CREATE", resource="user", selector="*",
        )
        owned_perm: PolicyContext = {
            "user": {"*": UPDATE | CREATE, },
        }
        assert is_write_allowed(owned_perm, create_user) is True

        # But we can't allow it to delete anything.
        delete_user = AccessRequest(
            operation="DELETE", resource="user", selector="*",
        )
        assert is_write_allowed(owned_perm, delete_user) is False

    def test_update_coupon_with_all_policy(self):
        "User tries to update a specific coupon with all policies"
        update_coupon = AccessRequest(
            operation="UPDATE", resource="coupon", selector="43df",
        )
        owned_perm = {
            "coupon": {"*": READ | UPDATE | DELETE, },
        }
        assert is_write_allowed(owned_perm, update_coupon) is True

        # But we can't allow it to create coupons.
        create_coupon = AccessRequest(
            operation="CREATE", resource="coupon", selector="*",
        )
        assert is_write_allowed(owned_perm, create_coupon) is False

    def test_delete_user_specific_with_enough_privilege(self):
        "Tries to delete a specific user with specific policy"
        delete_user = AccessRequest(
            operation="DELETE", resource="user", selector="3dc4",
        )
        owned_perm = {
            "user": {"*": CREATE | UPDATE, "3dc4": DELETE},
        }
        assert is_write_allowed(owned_perm, delete_user) is True

        update_user = AccessRequest(
            operation="UPDATE", resource="user", selector="3dc4",
        )

        assert is_write_allowed(owned_perm, update_user) is True
