import uuid
from datetime import datetime
from typing import Any, List, Optional, Callable

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import events, mapper, relationship

from src.auth.domain import model


users: Callable[[MetaData], Table] = lambda metadata: Table(
    "users",
    metadata,
    Column(
        "id",
        String(64),
        primary_key=True,
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
    ),
    Column(
        "access_key",
        String(255),
        nullable=False,
        unique=True,
    ),
    Column("name", String(255), nullable=True),
    Column("email", String(255), nullable=False),
    Column("password", Text, nullable=False),
    Column(
        "created_at",
        TIMESTAMP,
        nullable=False,
        default=lambda: datetime.today(),
    ),
    Column("id_role", String(64), ForeignKey("roles.id"), nullable=True),
)

permissions: Callable[[MetaData], Table] = lambda metadata: Table(
    "permissions",
    metadata,
    Column(
        "id",
        String(64),
        primary_key=True,
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
    ),
    Column("resource", String(128), nullable=False),
    Column("action", Enum(model.PermissionActionEnum), nullable=False),
    Column("is_conditional", Boolean(), nullable=False),
    UniqueConstraint("resource", "action", "is_conditional"),
)

roles: Callable[[MetaData], Table] = lambda metadata: Table(
    "roles",
    metadata,
    Column(
        "id",
        String(64),
        primary_key=True,
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
    ),
    Column("code", String(128), nullable=False, unique=True, primary_key=True),
    Column("name", String(256), nullable=False),
    Column(
        "created_at",
        TIMESTAMP,
        nullable=False,
        default=lambda: datetime.today(),
    ),
)

role_permissions: Callable[[MetaData], Table] = lambda metadata: Table(
    "role_permissions",
    metadata,
    Column(
        "id_role", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "id_permission",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_permissions: Callable[[MetaData], Table] = lambda metadata: Table(
    "user_permissions",
    metadata,
    Column(
        "id_user", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "id_permission",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


def start_mappers(metadata) -> None:
    mapper(model.Permission, permissions(metadata))
    mapper(
        model.Role,
        roles(metadata),
        properties={
            "permissions": relationship(
                model.Permission,
                secondary=role_permissions(metadata),
                uselist=True,
                cascade="all",
                collection_class=set,
            )
        },
    )
    mapper(
        model.User,
        users(metadata),
        properties={
            "role": relationship(model.Role, uselist=False),
            "permissions": relationship(
                model.Permission,
                secondary=user_permissions(metadata),
                uselist=True,
                cascade="all",
                collection_class=set,
            ),
        },
    )


@events.event.listens_for(model.User, "load")
@events.event.listens_for(model.Role, "load")
def dynamic_attributes(aggregate, _: Any) -> None:
    aggregate._events = []
