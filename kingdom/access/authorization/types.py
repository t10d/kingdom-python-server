from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, NamedTuple, Tuple, Union

TOKEN_ALL = "*"


class Permission(Enum):
    """Fine-grained mapping of a permission."""

    READ = 0b000
    CREATE = 0b001
    UPDATE = 0b010
    DELETE = 0b100

    def __hash__(self) -> int:
        return hash(self.value)

    def __or__(self, other):
        if isinstance(other, Permission):
            other = other.value
        return self.value | other

    def __ror__(self, other):
        return self.__or__(other)

    def __and__(self, other):
        if isinstance(other, Permission):
            other = other.value
        return self.value & other

    def __rand__(self, other):
        return self.__and__(other)


@dataclass
class Resource:
    """An enterprise-wide resource wrapper"""

    name: str

    def __init__(self, name: str):
        self.name = name
        self.alias = name.lower()


@dataclass
class Conditional:
    """One and only one conditional clause"""

    identifier: str
    selector: str


@dataclass
class Policy:
    """
    Aggregate of authorization module.

    An association of permissions that are allowed to be performed on
    on instances of a given resource that match ANY of the conditionals
    criteria"""

    resource: Resource
    permissions: Tuple[Permission]
    conditionals: List[Conditional]


@dataclass
class AccessRequest:
    operation: int
    resource: str
    selector: str

    def __init__(
        self, operation: Permission, resource: Resource, selector: str
    ):
        self.operation = operation.value
        self.resource = resource.alias
        self.selector = selector

    def is_request_read(self) -> bool:
        return self.operation == 0


ResourceAlias = str
Selector = str
SelectorPermissionMap = Dict[Selector, Tuple[Permission, ...]]
PolicyContext = Dict[ResourceAlias, SelectorPermissionMap]

PermissionRaw = int
PermissionMap = Dict[Selector, PermissionRaw]
PolicyContextRaw = Dict[ResourceAlias, PermissionMap]
