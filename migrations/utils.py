import sqlalchemy as sa
from sqlalchemy import Table
from alembic import op
from typing import List, Dict

from apolo import config

access_key, _ = config.default_user()


def get_permissions_table() -> Table:
    return sa.sql.table(
        "permissions",
        sa.sql.column("id", sa.String),
        sa.sql.column("resource", sa.String),
        sa.sql.column("action", sa.String),
        sa.sql.column("is_conditional", sa.Boolean),
    )


def insert_permissions(permissions: List[Dict]) -> None:
    permissions_table = get_permissions_table()
    op.bulk_insert(
        permissions_table,
        permissions,
    )

    op.execute(
        f"""
        INSERT INTO user_permissions (
            SELECT u.id AS id_user, p.id AS id_permission
            FROM users u CROSS JOIN permissions p
            WHERE u.access_key = '{access_key}' AND p.id NOT IN (
                SELECT up.id_permission FROM user_permissions up 
                WHERE up.id_user = u.id 
            )
        )
        """
    )
