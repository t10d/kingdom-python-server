from kingdom.access.base import (
    Permission,
    Policy,
    Resource,
    Role,
    Statement,
    User,
)

CREATE = Permission.CREATE | 0
READ = Permission.READ | 0
UPDATE = Permission.UPDATE | 0
DELETE = Permission.DELETE | 0


def test_simple_policy_packing():
    """Given a list of Policies with no overlapping conditional statements,
    we expect a well-formatted map"""

    # Define policies
    product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.UPDATE,),
        conditionals=[
            Statement("resource.id", "ab4f"),
            Statement("resource.id", "13fa"),
        ],
    )

    ya_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.CREATE,),
        conditionals=[Statement("resource.id", "*"), ],
    )

    # Define domain roles
    store_manager = Role(
        "Store management group", policies=[product_policy, ya_product_policy]
    )

    account_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.READ,),
        conditionals=[Statement("resource.id", "*"), ],
    )

    ya_account_policy = Policy(
        resource=Resource("Account"),
        permissions=(Permission.UPDATE,),
        conditionals=[
            Statement("resource.id", "0bf3"),
            Statement("resource.id", "bc0e"),
        ],
    )

    # Define domain roles
    site_manager = Role(
        name="Site management group",
        policies=[account_policy, ya_account_policy, ],
    )

    # A ficticious manager
    user = User("abbf", roles=[store_manager, site_manager])

    policy_ctx = {
        "product": {"*": 1, "ab4f": 2, "13fa": 2, },
        "account": {"*": 0, "0bf3": 2, "bc0e": 2, },
    }

    assert user.policy_context == policy_ctx


def test_cumulative_policy_packing():
    """Given a list of Policies with cumulative conditional statements,
    we expect a well-formatted and cohesive map"""

    product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ,),
        conditionals=[Statement("resource.id", "*"), ],
    )

    ya_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.CREATE,),
        conditionals=[Statement("resource.id", "*"), ],
    )

    # Define domain role
    store_manager = Role(
        "Store management group", policies=[product_policy, ya_product_policy]
    )

    christmas_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.UPDATE,),
        conditionals=[
            Statement("resource.id", "044e"),
            Statement("resource.id", "0e0e"),
            Statement("resource.id", "bc0e"),
        ],
    )
    ya_christmas_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.DELETE, Permission.UPDATE),
        conditionals=[Statement("resource.id", "044e"), ],
    )

    yaa_christmas_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.DELETE,),
        conditionals=[
            Statement("resource.id", "bc0e"),
            Statement("resource.id", "aac0"),
        ],
    )

    # Define more fine-grained roles
    christmas_ops = Role(
        "Christmas task-force operations",
        policies=[
            christmas_policy,
            ya_christmas_policy,
            yaa_christmas_policy,
        ],
    )

    # A ficticious supervisor
    user = User("abbf", roles=[store_manager, christmas_ops])
    policy_ctx = {
        "product": {"*": 1, "044e": 6, "0e0e": 2, "bc0e": 6, "aac0": 4, }
    }
    assert user.policy_context == policy_ctx


def test_redundant_policy_packing():
    """Given a list of Policies with overlapping conditional statements,
    we expect a well-formatted without redundant statements map"""

    product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.CREATE, Permission.UPDATE),
        conditionals=[Statement("resource.id", "*"), ],
    )
    product_maint = Policy(
        resource=Resource("Product"),
        permissions=(Permission.UPDATE,),
        conditionals=[Statement("resource.id", "*")],
    )

    store_manager = Role(
        "Store management group", policies=[product_policy, product_maint]
    )

    ya_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ, Permission.DELETE),
        conditionals=[
            Statement("resource.id", "7fb4"),
            Statement("resource.id", "49f3"),
            Statement("resource.id", "abc9"),
        ],
    )

    yao_product_policy = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ, Permission.UPDATE,),
        conditionals=[
            Statement("resource.id", "aaa"),
            Statement("resource.id", "abc9"),
        ],
    )

    electronic_manager = Role(
        "Electronic sales group",
        policies=[ya_product_policy, yao_product_policy],
    )

    sales_coord = User("0bf3", roles=[electronic_manager, store_manager])

    policy_ctx = {
        "product": {"*": 3, "7fb4": 4, "49f3": 4, "abc9": 4},
    }

    assert sales_coord.policy_context == policy_ctx
