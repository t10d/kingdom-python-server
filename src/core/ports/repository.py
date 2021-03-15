import abc
from typing import List, Set

from sqlalchemy import orm

from src.core.domain import Aggregate


class AbstractRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[Aggregate] = set()

    def add(self, aggregate: Aggregate) -> None:
        self.seen.add(aggregate)
        self._add(aggregate)

    def get(self, _id: str) -> Aggregate:
        aggregate = self._get(_id)
        if aggregate:
            self.seen.add(aggregate)
        return aggregate

    @abc.abstractmethod
    def list(self) -> List[Aggregate]:
        raise NotImplementedError

    @abc.abstractmethod
    def _add(self, aggregate: Aggregate) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, aggregate: str) -> Aggregate:
        raise NotImplementedError


class AbstractSqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: orm.Session):
        self.session = session
        super().__init__()

    def list(self):
        raise NotImplementedError

    def _add(self, entity: Aggregate):
        raise NotImplementedError

    def _get(self, _id: str):
        raise NotImplementedError
