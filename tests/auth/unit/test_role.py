from src.auth.domain import model
from tests.auth import helpers


def test_role_equality():
    code = helpers.random_word()
    a_role = model.Role(
        name=helpers.random_word(), code=code, permissions=set()
    )
    b_role = model.Role(
        name=helpers.random_word(), code=code, permissions=set()
    )
    assert a_role == b_role


def test_attach_permissions():
    permission_1 = model.Permission(
        "wallet", model.PermissionActionEnum.CREATE, False
    )
    permission_2 = model.Permission(
        "wallet", model.PermissionActionEnum.CREATE, True
    )
    role = model.Role(
        name=helpers.DEFAULT_ROLE_NAME,
        code=helpers.DEFAULT_ROLE_CODE,
        permissions=set(),
    )
    role.attach_permissions({permission_1, permission_2})
    assert len(role.permissions) > 0
    assert role.permissions == {permission_1, permission_2}


def test_detach_permissions():
    permission_1 = model.Permission(
        resource="wallet",
        action=model.PermissionActionEnum.CREATE,
        is_conditional=False,
    )
    permission_2 = model.Permission(
        resource="wallet",
        action=model.PermissionActionEnum.CREATE,
        is_conditional=True,
    )
    role = model.Role(
        name=helpers.DEFAULT_ROLE_NAME,
        code=helpers.DEFAULT_ROLE_CODE,
        permissions={permission_1, permission_2},
    )
    assert len(role.permissions) == 2
    role.detach_permissions({permission_1})
    assert len(role.permissions) == 1
