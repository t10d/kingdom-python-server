import re
import enum
import jwt
from dataclasses import dataclass
from typing import Any, Optional, Set, List
# TODO we shouldn't be importing any of these below here
from passlib.context import CryptContext
from datetime import datetime, timedelta
from string import Template
from pathlib import Path

from src.core import domain, utils
from src.auth import config

crypt = CryptContext(schemes=["bcrypt"], deprecated="auto")

regex = r"[^@]+@[^@]+\.[^@]+"


class PermissionActionEnum(enum.Enum):
    LIST = "LIST"
    GET = "GET"
    CREATE = "CREATE"
    UPDATE = "UPDATE"


class Permission(domain.Entity):
    resource: str
    action: PermissionActionEnum
    is_conditional: bool

    def __init__(self, resource: str, action: str, is_conditional: bool):
        self.resource = resource
        self.action = PermissionActionEnum(action)
        self.is_conditional = is_conditional

    def __eq__(self, other):
        return (
            isinstance(other, Permission)
            and self.resource == other.resource  # noqa W503
            and self.action == other.action  # noqa W503
            and self.is_conditional == other.is_conditional  # noqa W503
        )

    def __hash__(self):
        return hash((self.resource, self.action, self.is_conditional))

    def __repr__(self):
        return f"{type(self.action)} {self.resource} {self.is_conditional}"


class Role(domain.Aggregate):
    code: str
    name: str
    permissions: Set[Permission]

    def __init__(
        self, code: str, name: str, permissions: Optional[Set] = None
    ):
        self.code = code
        self.name = name
        self.permissions = {} or permissions
        super().__init__()

    def __eq__(self, other):
        return isinstance(other, Role) and self.code == other.code

    def __hash__(self):
        return hash(self.code)

    def attach_permissions(self, permissions: Set[Permission]):
        self.permissions = self.permissions | permissions

    def detach_permissions(self, permissions: Set[Permission]):
        self.permissions = self.permissions - permissions


class User(domain.Aggregate):
    access_key: str
    email: str
    name: str
    password: str
    permissions: Set[Permission]
    role: Optional[Role]

    def __init__(self, access_key: str, name: str, email: str, password: str):
        self.access_key = access_key
        self.name = name
        self.email = email
        self.password = User.hash_password(password)
        self.role = None
        self.permissions = set()
        super().__init__()

    def __repr__(self) -> str:
        return f"<User {self.access_key}>"

    def __hash__(self) -> int:
        return hash(self.access_key)

    def __eq__(self, other: Any) -> Any:
        return other.access_key == self.access_key

    @staticmethod
    def hash_password(password: str) -> Any:
        return crypt.hash(password)

    def is_correct_password(self, password: str) -> bool:
        return bool(crypt.verify(password, self.password))

    def is_email_valid(self) -> bool:
        if re.match(regex, self.email):
            return True
        return False

    def change_password(self, new_password: str) -> None:
        self.password = self.hash_password(new_password)

    def generate_password_reset_token(self) -> bytes:
        now = datetime.utcnow()
        expiration: datetime = now + timedelta(
            minutes=config.get_jwt_token_expiration()
        )
        payload: dict = dict(
            sub=self.password,
            exp=expiration,
            access_key=self.access_key,
            nbf=now,
        )
        encoded_jwt = jwt.encode(
            payload=payload,
            key=config.get_jwt_secret_key(),
            algorithm=config.JWT_ALGORITHM,
        )
        return encoded_jwt.decode("utf-8")

    def generate_reset_pwd_email(self, client_url: str) -> str:
        # TODO This method should be inside a proper adapter
        with open(Path(config.EMAIL_TEMPLATES_DIR) / "reset_pwd.html") as f:
            template_str = f.read()

        token = self.generate_password_reset_token()
        link = f"{client_url}redefinicao-senha?token={token}"
        environment: dict = dict(
            username=self.name,
            valid_minutes=config.DEFAULT_TOKEN_EXPIRATION,
            link=link,
        )
        return Template(template_str).substitute(**environment)

    def pack_authentication_secret(self) -> bytes:
        expiration: datetime = datetime.utcnow() + timedelta(
            minutes=config.get_jwt_token_expiration()
        )
        payload: dict = dict(sub=self.access_key, exp=expiration)
        return jwt.encode(
            payload=payload,
            key=config.get_jwt_secret_key(),
            algorithm=config.JWT_ALGORITHM,
        )

    def is_allowed_to(self, action: str, resource: str):
        return bool(self.get_user_permission(action, resource))

    def get_user_permission(self, action: str, resource: str):
        return utils.ifilter(
            self.permissions,
            lambda p: p.action.value == action and p.resource == resource,
        )

    def attach_permissions(self, permissions: Set[Permission]):
        self.permissions = self.permissions | permissions

    def detach_permissions(self, permissions: Set[Permission]):
        self.permissions = self.permissions - permissions

    def set_role(self, role: Role, override_permissions: bool):
        self.role = role
        if override_permissions:
            self.permissions = role.permissions
