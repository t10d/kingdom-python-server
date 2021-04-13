from datetime import datetime, timedelta
from typing import Dict, Generator, List, Optional, Tuple

import jwt

from kingdom.access.authorization.encode import encode
from kingdom.access.authorization.types import (
    Conditional,
    Permission,
    Policy,
    PolicyContext,
    Resource,
    dataclass,
)

RANDOM_KEY = "abcd00f"
JWT_ALGORITHM = "HS256"

TOKEN_EXPIRATION_MIN = 30


@dataclass
class Role:
    name: str
    policies: List[Optional[Policy]]

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class User:
    access_key: str
    roles: List[Optional[Role]]

    def resolve_policies(self):
        # TODO: Improve this typing
        for role in self.roles:
            for policy in role.policies:
                yield policy


JWTDecodedPayload = Dict

MaybeBytes = Tuple[Optional[bytes], Optional[Exception]]
MaybePayload = Tuple[Optional[JWTDecodedPayload], Optional[Exception]]


def encode_user_policies(user: User) -> PolicyContext:
    user_policies = list(user.resolve_policies())
    return encode(user_policies)


def encode_user_payload(user: User) -> JWTDecodedPayload:
    expiration = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_MIN)
    return dict(
        sub=user.access_key, exp=expiration, roles=encode_user_policies(user),
    )


def encode_jwt(user: User) -> MaybeBytes:
    payload = encode_user_payload(user)
    try:
        return (
            jwt.encode(
                payload=payload, key=RANDOM_KEY, algorithm=JWT_ALGORITHM
            ),
            None,
        )
    except jwt.PyJWTError as exc:
        return None, exc


def decode_jwt(token: bytes) -> MaybePayload:
    try:
        return (
            jwt.decode(jwt=token, key=RANDOM_KEY, algorithms=[JWT_ALGORITHM]),
            None,
        )
    except jwt.PyJWTError as exc:
        return None, exc
