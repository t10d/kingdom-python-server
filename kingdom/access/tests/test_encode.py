from kingdom.access.authorization.encode import encode
from kingdom.access.authorization.model import (
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
        "product": {
            "*": (Permission.CREATE,),
            "ab4f": (Permission.UPDATE,),
            "13fa": (Permission.UPDATE,),
        },
        "account": {
            "*": (Permission.READ,),
            "0bf3": (Permission.UPDATE,),
            "bc0e": (Permission.UPDATE,),
        },
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
        "product": {
            "*": (Permission.READ, Permission.CREATE,),
            "7fb4": (Permission.UPDATE,),
            "49f3": (Permission.UPDATE,),
            "abc9": (Permission.UPDATE, Permission.DELETE),
            "aaa": (Permission.DELETE,),
        },
    }

    assert encode(role_policies) == owned_perm
