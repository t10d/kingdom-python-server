import os
from typing import Any

POSTGRES_URI_TEMPLATE = "postgresql://{}:{}@{}:{}/{}"

PG_USER = os.environ.get("POSTGRES_USER", "postgres")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_PORT = os.environ.get("POSTGRES_PORT", 5432)
PG_DB = os.environ.get("POSTGRES_DB", "template")

POSTGRES_DEFAULT = (
    PG_USER,
    PG_PASSWORD,
    PG_HOST,
    PG_PORT,
    PG_DB
)


def default_user() -> tuple:
    return "admin@t10.digital", "admin"


def default_role() -> tuple:
    return "adm", "Administrator"


def get_postgres_uri() -> str:
    return os.environ.get(
        "DATABASE_URL", POSTGRES_URI_TEMPLATE.format(*POSTGRES_DEFAULT)
    )


def get_envar(key: str, default: Any = None) -> Any:
    return os.environ.get(key, default)


def current_environment() -> str:
    return str(get_envar("ENVIRONMENT", "LOCAL")).lower()
