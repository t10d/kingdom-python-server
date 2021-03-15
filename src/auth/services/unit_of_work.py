from typing import Any, Generator

from craftship.auth.adapters import repository
from craftship.core.ports import unit_of_work


class AuthSqlAlchemyUnitOfWork(unit_of_work.SqlAlchemyUnitOfWork):
    def collect_new_events(self) -> Generator:
        dirty = self.users.seen | self.roles.seen
        for aggregate in dirty:
            while aggregate._events:
                yield aggregate._events.pop(0)

    def __enter__(self) -> Any:
        self.session = self.session_factory()
        self.users = repository.UserSqlAlchemyRepository(self.session)
        self.roles = repository.RoleSqlAlchemyRepository(self.session)
        self.permissions = repository.PermissionSqlAlchemyRepository(
            self.session
        )
        return super().__enter__()
