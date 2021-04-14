from dataclasses import dataclass
from typing import List

from kingdom.access.authentication.types import decode_jwt
from kingdom.access.authorization.types import AccessRequest
from kingdom.access.authorization.verify import (
    check_read_permission,
    check_write_permission,
)


@dataclass
class AuthFlow:
    JWT: bytes
    context: AccessRequest

    def authenticate(self) -> None:
        payload, err = decode_jwt(self.JWT)
        if err:
            self._is_authenticated = False
        else:
            self._payload = payload
            self._is_authenticated = True

    @property
    def is_authenticated(self) -> bool:
        if not hasattr(self, "_is_authenticated"):
            self.authenticate()
        return self._is_authenticated

    @property
    def is_authorized(self) -> bool:
        if not hasattr(self, "_is_authorized"):
            self.authorize()
        return self._is_authorized

    def scope(self) -> List:
        # TODO: Scope should be a class
        # Scope(operation="READ", resource="product", instances=["ffff"])
        return self._scope

    def __resolve_read_authorization(self) -> None:
        self._is_authorized = True
        owned_permissions = self._payload["roles"]
        self._scope = check_read_permission(owned_permissions, self.context)

    def __resolve_write_authorization(self) -> None:
        owned_permissions = self._payload["roles"]
        self._is_authorized = check_write_permission(
            owned_permissions, self.context
        )
        if self._is_authorized:
            self._scope = [self.context.selector]
        else:
            self._scope = []

    def authorize(self) -> None:
        """Can either be read/write"""
        if self.context.is_request_read():
            # The restriction comes on scope
            self.__resolve_read_authorization()
        else:
            self.__resolve_write_authorization()
