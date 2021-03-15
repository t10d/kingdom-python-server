from typing import Any

from craftship.auth.domain import model
from craftship.core.ports.repository import AbstractSqlAlchemyRepository


class UserSqlAlchemyRepository(AbstractSqlAlchemyRepository):
    def __init__(self, session):
        super().__init__(session)

    def list(self) -> Any:
        return self.session.query(model.User).all()

    def _add(self, user: model.User) -> None:
        self.session.add(user)

    def _get(self, access_key: str) -> model.User:
        return (
            self.session.query(model.User)
            .filter(model.User.access_key == access_key)
            .first()
        )


class RoleSqlAlchemyRepository(AbstractSqlAlchemyRepository):
    def list(self):
        return self.session.query(model.Role).all()

    def _add(self, role: model.Role) -> None:
        self.session.add(role)

    def _get(self, code: str) -> model.Role:
        return (
            self.session.query(model.Role)
            .filter(model.Role.code == code)
            .first()
        )


class PermissionSqlAlchemyRepository(AbstractSqlAlchemyRepository):
    def list(self):
        return self.session.query(model.Permission).all()

    def _add(self, _) -> None:
        pass

    def _get(self, _) -> None:
        pass
