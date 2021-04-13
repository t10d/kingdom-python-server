import jwt
from graphql import GraphQLError

from src.auth import config
from src.core.exceptions import ServerException

# TODO This should be inside handlers
class InvalidToken(ServerException):
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
