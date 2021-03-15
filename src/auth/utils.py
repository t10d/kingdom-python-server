import jwt
from graphql import GraphQLError

from craftship.auth import config
from craftship.core.exceptions import ApoloException


class InvalidToken(ApoloException):
    def __init__(self):
        super().__init__("Invalid Token")


def parse_token(token: str) -> dict:
    try:
        return jwt.decode(
            jwt=token,
            key=config.get_jwt_secret_key(),
            algorithms=config.JWT_ALGORITHM,
        )
    except jwt.PyJWTError:
        raise InvalidToken()
