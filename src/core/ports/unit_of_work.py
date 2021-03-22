import abc
from typing import Callable, Generator

from src import orm
from src.core.ports import repository



class AbstractUnitOfWork(abc.ABC):
    def __enter__(self):  # type: ignore
        return self

    def __exit__(self, *args):  # type: ignore
        self.rollback()

    @abc.abstractmethod
    def collect_new_events(self) -> Generator:
        """Connects events raised from Domain Layer to the Message Bus

        Message Bus calls this method to handle any new event that might
        have been raised after a command was ran"""
        raise NotImplementedError

    def commit(self) -> None:
        """Every time a commit is made, we try to commit current database
        transaction"""
        self._commit()
        # self.publish_events()

    @abc.abstractmethod
    def _commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    session: orm.Session

    def __init__(self, session_factory: Callable = orm.DEFAULT_SESSION_FACTORY):
        self.session_factory: Callable = session_factory

    def __exit__(self, *args):  # type: ignore
        super().__exit__(*args)
        self.session.close()

    def _commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
