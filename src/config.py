import os
from typing import Any

POSTGRES_URI_TEMPLATE = "postgresql://{}:{}@{}:{}/{}"
POSTGRES_DEFAULT = ("postgres", "", "localhost", 5432, "apolo")


def default_user() -> tuple:
    return "admin@npl.com.br", "admin"


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
