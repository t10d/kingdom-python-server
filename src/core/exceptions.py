from typing import Union, Dict, Type
from graphql import GraphQLError


class ApoloException(Exception):
    def __init__(self, msg: str):
        self.message = f"{self.__class__.__name__}: {msg}"


def resolve_error(
    error: Union[Exception, ApoloException], error_resolver: Dict
) -> GraphQLError:
    message = (
        error.message if isinstance(error, ApoloException) else str(error)
    )
    status = error_resolver.get(type(error), "UNKNOWN_ERROR")
    return GraphQLError(message, extensions=dict(status=status))
