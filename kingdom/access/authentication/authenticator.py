"""
authenticator.py
Handles authentication throughout services
"""
from dataclasses import dataclass
from typing import Dict

import jwt

from src.core import config


class InvalidToken(Exception):
    def __init__(self):
        super().__init__("Invalid JWT token.")


@dataclass
class JWT:
    "Simple JWT Wrapper"
    token: str

    def decode(self) -> Dict:
        """Decodes a JWT"""
        try:
            self.payload = jwt.decode(
                jwt=self.token,
                key=config.get_jwt_secret_key(),
                algorithms=config.JWT_ALGORITHM,
            )
            return self.payload
        except jwt.PyJWTError:
            raise InvalidToken()


class Authenticator:
    token: JWT
    payload: Dict

    def __init__(self, token: str):
        self.jwt = JWT(token)

    def __call__(self):
        self.payload = self.jwt.decode()


def test_authenticator():
    token = "abr9f8c09adj!lsd.sdxxf.ldfj"
    auth = Authenticator(token)
    assert auth()
