from typing import List, Optional, Generator, Any, Callable

from craftship.core.ports import unit_of_work, repository, email_sender
from craftship.core.domain import Aggregate
from craftship.auth.domain import model

from apolo import config


class FakeUserRepository(repository.AbstractRepository):
    users: model.User = []

    def list(self) -> model.User:
        return FakeUserRepository.users

    def _add(self, user: model.User) -> None:
        FakeUserRepository.users.append(user)

    def _get(self, access_key: str) -> model.User:
        try:
            return next(
                filter(
                    lambda user: user.access_key == access_key,
                    FakeUserRepository.users,
                )
            )
        except StopIteration:
            return None

    def get(self, access_key: str):
        user = self._get(access_key)
        return user

    def __repr__(self) -> str:
        return f"<Users {self.users}>"


class FakeRoleRepository(repository.AbstractRepository):
    roles: List[model.Role] = []

    def list(self) -> List[model.Role]:
        return FakeRoleRepository.roles

    def _add(self, role: model.Role) -> None:
        FakeRoleRepository.roles.append(role)

    def _get(self, code: str) -> Optional[model.Role]:
        try:
            return next(
                filter(lambda r: r.code == code, FakeRoleRepository.roles)
            )
        except StopIteration:
            return None


class FakePermissionRepository(repository.AbstractRepository):
    def list(self) -> List[model.Permission]:
        return [model.Permission(**p) for p in AVAILABLE_PERMISSIONS]

    def _add(self, _) -> None:
        pass

    def _get(self, _) -> None:
        pass


class FakeUserUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.users = FakeUserRepository()
        self.roles = FakeRoleRepository()
        self.permissions = FakePermissionRepository()

    def _commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def collect_new_events(self) -> Generator:
        dirty = self.users.seen | self.roles.seen
        for aggregate in dirty:
            while aggregate._events:
                yield aggregate._events.pop(0)


class FakeEmailSender(email_sender.AbstractEmailSender):
    sent: bool = False

    def __init__(self):
        pass

    def send_email(
        self,
        email_to: str,
        subject: str,
        template: str,
    ) -> int:
        FakeEmailSender.sent = True
        return 250


AVAILABLE_PERMISSIONS_GRAPHQL = [
    {"resource": "user", "action": "CREATE", "isConditional": False},
    {"resource": "role", "action": "LIST", "isConditional": False},
    {"resource": "role", "action": "UPDATE", "isConditional": False},
    {"resource": "role", "action": "CREATE", "isConditional": False},
]

AVAILABLE_PERMISSIONS = [
    {"resource": "user", "action": "CREATE", "is_conditional": False},
    {"resource": "role", "action": "LIST", "is_conditional": False},
    {"resource": "role", "action": "UPDATE", "is_conditional": False},
    {"resource": "role", "action": "CREATE", "is_conditional": False},
]
