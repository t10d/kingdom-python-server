from typing import List, Dict, Optional, Any

from src.core.utils import group_rows, create_connection
from src.auth.services import unit_of_work


def query_role(
    code: str, uow: unit_of_work.AuthSqlAlchemyUnitOfWork
) -> Optional[Dict]:
    with uow:
        role_permissions = uow.session.execute(
            """
            SELECT
                r.name              as name,
                r.code              as code,
                r.created_at        as created_at,
                p.resource          as resource,
                p.action            as action,
                p.is_conditional    as is_conditional
            FROM
                roles r
                LEFT JOIN role_permissions rp ON r.id = rp.id_role
                LEFT JOIN permissions p ON rp.id_permission = p.id
            WHERE r.code = :code
            """,
            dict(code=code),
        )
    rows_role = [dict(rp) for rp in role_permissions]
    if not rows_role:
        return None
    return group_rows(
        rows=rows_role,
        identifier="code",
        group_key="permissions",
        keys_to_flat={"name", "code", "created_at"},
        keys_to_group={"resource", "action", "is_conditional"},
    ).pop()


@create_connection
def query_roles(
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
    pagination_info: Dict,
    name: str = "",
) -> Any:
    with uow:
        roles = uow.session.execute(
            """
            SELECT *, COUNT(*) OVER() AS elements_count
            FROM roles
            WHERE name ILIKE :name
            LIMIT :limit
            OFFSET :offset
            """,
            dict(
                name=f"%{name}%",
                offset=pagination_info["offset"],
                limit=pagination_info["limit"],
            ),
        )
    return [dict(role) for role in roles]


@create_connection
def query_permissions(
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
    pagination_info: Dict,
    resource: str = "",
    action: str = "",
) -> Any:
    with uow:
        permissions = uow.session.execute(
            """
            SELECT *, COUNT(*) OVER() AS elements_count
            FROM permissions
            WHERE resource ILIKE :resource AND action::text ILIKE :action
            ORDER BY resource, action
            LIMIT :limit
            OFFSET :offset
            """,
            dict(
                resource=f"%{resource}%",
                action=f"%{action}%",
                offset=pagination_info["offset"],
                limit=pagination_info["limit"],
            ),
        )
    return [dict(p) for p in permissions]


def query_user(
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork,
    access_key: str,
) -> Optional[Dict]:
    with uow:
        info = uow.session.execute(
            """
            SELECT
                u.access_key        AS access_key,
                u.name              AS name,
                u.email             AS email,
                u.created_at        AS created_at,
                json_build_object('name', r.name, 'code', r.code) AS role,
                p.resource          AS resource,
                p.action            AS action,
                p.is_conditional    AS is_conditional
            FROM
                users u
                LEFT JOIN roles r ON u.id_role = r.id
                LEFT JOIN user_permissions up ON u.id = up.id_user
                LEFT JOIN permissions p ON up.id_permission = p.id
            WHERE access_key = :access_key
                """,
            dict(access_key=access_key),
        )
    rows_info = [dict(i) for i in info]
    if not rows_info:
        return None
    return group_rows(
        rows=rows_info,
        identifier="access_key",
        group_key="permissions",
        keys_to_flat={"access_key", "name", "email", "created_at", "role"},
        keys_to_group={"resource", "action", "is_conditional"},
    ).pop()


@create_connection
def query_users(
    uow: unit_of_work.AuthSqlAlchemyUnitOfWork, pagination_info: Dict
) -> Any:
    with uow:
        users = uow.session.execute(
            """
            SELECT access_key, name, email, created_at,
            COUNT(*) OVER() AS elements_count
            FROM users
            ORDER BY name
            LIMIT :limit
            OFFSET :offset
            """,
            dict(
                offset=pagination_info["offset"],
                limit=pagination_info["limit"],
            ),
        )
    return [dict(user) for user in users]
