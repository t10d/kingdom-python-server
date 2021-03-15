import base64
import os
import uuid

SCHEMA_PATHS = ("apolo/auth/entrypoint/graphql/schema.graphql",)

DEFAULT_TOKEN_EXPIRATION = 60
DEFAULT_JWT_SECRET_KEY = base64.b64encode(
    uuid.uuid4().hex[:7].encode("utf-8")
).decode("utf-8")
JWT_ALGORITHM = "HS256"
AUTH_TYPE = "Bearer"
EMAIL_TEMPLATES_DIR = "apolo/auth/services/email-templates"
SUBJECT_PWD_CHANGE = "Troca de Senha Apolo NPL"


def get_jwt_secret_key() -> str:
    return os.environ.get("JWT_SECRET_KEY", DEFAULT_JWT_SECRET_KEY)


def get_jwt_token_expiration() -> int:
    return int(
        os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", DEFAULT_TOKEN_EXPIRATION)
    )


def get_smtp_port() -> str:
    return os.environ.get("SMTP_PORT", None)


def get_smtp_pwd() -> str:
    return os.environ.get("SMTP_PASSWORD", None)


def get_smtp_host() -> str:
    return os.environ.get("SMTP_HOST", None)


def get_smtp_user() -> str:
    return os.environ.get("EMAILS_SENDER_EMAIL", None)


def get_email_name() -> str:
    return os.environ.get("EMAILS_FROM_NAME", "NPL")
