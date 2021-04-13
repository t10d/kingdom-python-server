from kingdom.access.authorization.encode import encode
from kingdom.access.authorization.types import (
    Conditional,
    Permission,
    Policy,
    PolicyContext,
    Resource,
    Selector,
)


def test_simple_policy_packing():
    """Given a list of Policies with no overlapping conditional selectors,
    we expect a well-formatted DTO dict"""
    product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.UPDATE,),
        conditionals=[
            Conditional("resource.id", "ab4f"),
            Conditional("resource.id", "13fa"),
        ],
    )

    ya_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.CREATE,),
        conditionals=[Conditional("resource.id", "*"), ],
    )

    account_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.READ,),
        conditionals=[Conditional("resource.id", "*"), ],
    )

    ya_account_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE,),
        conditionals=[
            Conditional("resource.id", "0bf3"),
            Conditional("resource.id", "bc0e"),
        ],
    )

    role_policies = [
        product_policy,
        ya_product_policy,
        account_policy,
        ya_account_policy,
    ]

    owned_perm = {
        "product": {"*": 1, "ab4f": 2, "13fa": 2, },
        "account": {"*": 0, "0bf3": 2, "bc0e": 2, },
    }

    assert encode(role_policies) == owned_perm


def test_cumulative_policy_packing():
    product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ,),
        conditionals=[Conditional("resource.id", "*"), ],
    )

    ya_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.CREATE,),
        conditionals=[Conditional("resource.id", "*"), ],
    )

    account_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.UPDATE,),
        conditionals=[
            Conditional("resource.id", "044e"),
            Conditional("resource.id", "0e0e"),
            Conditional("resource.id", "bc0e"),
        ],
    )

    ya_account_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.DELETE,),
        conditionals=[Conditional("resource.id", "044e"), ],
    )

    yaa_account_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.DELETE,),
        conditionals=[
            Conditional("resource.id", "bc0e"),
            Conditional("resource.id", "aac0"),
        ],
    )
    role_policies = [
        product_policy,
        ya_product_policy,
        account_policy,
        ya_account_policy,
        yaa_account_policy,
    ]
    owned_perm = {
        "product": {"*": 1, "044e": 6, "0e0e": 2, "bc0e": 6, "aac0": 4, }
    }
    assert encode(role_policies) == owned_perm


def test_redundant_policy_packing():
    """Given a list of Policies with overlapping conditional selectors,
    we expect a well-formatted DTO dict"""
    product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ, Permission.CREATE),
        conditionals=[Conditional("resource.id", "*"), ],
    )

    ya_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ, Permission.UPDATE),
        conditionals=[
            Conditional("resource.id", "7fb4"),
            Conditional("resource.id", "49f3"),
            Conditional("resource.id", "abc9"),
        ],
    )

    yao_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ, Permission.DELETE,),
        conditionals=[
            Conditional("resource.id", "aaa"),
            Conditional("resource.id", "abc9"),
        ],
    )

    role_policies = [
        product_policy,
        ya_product_policy,
        yao_product_policy,
    ]

    owned_perm = {
        "product": {"*": 1, "7fb4": 2, "49f3": 2, "abc9": 6, "aaa": 4, },
    }

    assert encode(role_policies) == owned_perm
