import pytest

from craftship.auth.domain import model
from craftship.auth import views
from craftship.auth.services import handlers
from tests.auth import helpers


@pytest.mark.asyncio
async def test_query_roles(dependencies):
    uow, _ = dependencies
    for i in range(20):
        handlers.create_role(**helpers.random_role(), permissions=[], uow=uow)
    pagination_info = {"limit": 10, "offset": 5}
    roles = views.query_roles(uow, pagination_info=pagination_info)
    assert roles
    assert roles["elements_count"] == helpers.query_roles_count(uow.session)
    assert len(roles["elements"]) == 10
    assert all([role["code"] and role["name"] for role in roles["elements"]])
    assert roles["page_info"]["has_next_page"] is True
    assert roles["page_info"]["start_offset"] == 5
    assert roles["page_info"]["end_offset"] == 15


@pytest.mark.asyncio
async def test_query_role(dependencies):
    uow, _ = dependencies
    handlers.create_role(
        code="test",
        name="test",
        permissions=[
            {
                "resource": "user",
                "action": model.PermissionActionEnum.CREATE,
                "is_conditional": False,
            },
            {
                "resource": "user",
                "action": model.PermissionActionEnum.UPDATE,
                "is_conditional": False,
            },
        ],
        uow=uow,
    )

    role = views.query_role("test", uow)
    assert role
    assert role["code"] == "test"
    assert len(role["permissions"]) == 2
    assert all(
        [
            permission["resource"] == "user"
            and (
                permission["action"] == "CREATE"
                or permission["action"] == "UPDATE"
            )
            for permission in role["permissions"]
        ]
    )


def test_query_permissions(dependencies):
    uow, _ = dependencies
    pagination_info = {"limit": None, "offset": 0}
    permissions = views.query_permissions(
        uow=uow, pagination_info=pagination_info
    )
    assert permissions
    assert all(
        [
            p["resource"] and p["action"] and p["is_conditional"] is not None
            for p in permissions["elements"]
        ]
    )

    filtered_permissions = [
        p for p in permissions["elements"] if p["action"] == "CREATE"
    ]

    create_permissions = views.query_permissions(
        uow=uow, pagination_info=pagination_info, action="CREATE"
    )
    assert len(filtered_permissions) == create_permissions["elements_count"]
