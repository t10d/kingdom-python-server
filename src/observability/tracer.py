import abc
from contextvars import Context
from typing import Callable


class AbstractTracerDelegate(abc.ABC):
    @abc.abstractmethod
    def trace(self, name: str, block: Callable, *args, **kwargs):
        """
        Calculate and records the execution for the given block.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def add_property(self, key: str, value: str):
        """
        Add a key/value pair to the current span.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def span_failure(self, ex: Exception, expected: bool):
        """
        Notify an error for the current span.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError


class AbstractTracer(abc.ABC):
    @abc.abstractmethod
    def for_context(self, context: Context):
        raise NotImplementedError

    @abc.abstractmethod
    def operation_name(self, name: str) -> AbstractTracerDelegate:
        """
        Defines the operation name for the current span.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def add_property(self, key: str, value: str):
        """
        Add a key/value pair to the current span.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError
