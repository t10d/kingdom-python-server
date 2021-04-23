from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import jwt
from kingdom.access import config
from kingdom.access.types import JWT, Payload

MaybeJWT = Tuple[Optional[JWT], Optional[Exception]]
MaybePayload = Tuple[Optional[Payload], Optional[Exception]]


class InvalidToken(Exception):
    def __init__(self):
        super().__init__("Unauthorized: Invalid token.")


def encode(payload: Payload) -> JWT:
    try:
        return jwt.encode(
            payload=payload,
            key=config.RANDOM_KEY,
            algorithm=config.JWT_ALGORITHM,
        )

    except jwt.PyJWTError:
        raise


def decode(token: JWT) -> Payload:
    try:
        return jwt.decode(
            jwt=token,
            key=config.RANDOM_KEY,
            algorithms=[config.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise InvalidToken()
