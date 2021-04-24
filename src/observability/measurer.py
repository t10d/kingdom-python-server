import abc


class AbstractMeasurerDelegate(abc.ABC):
    """
    Abstract class implemented by the actual measurer.
    """

    @abc.abstractmethod
    def count(self):
        raise NotImplementedError

    @abc.abstractmethod
    def inc(self):
        raise NotImplementedError

    @abc.abstractmethod
    def dec(self):
        raise NotImplementedError

    @abc.abstractmethod
    def observe(self):
        raise NotImplementedError

    @abc.abstractmethod
    def observe_bucket(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError


class AbstractMeasurer(abc.ABC):
    """
    Abstract class that must be implemented by tools used for measurement.
    This is used to keep tracking of how many times a function is used and
    to export this information.
    """

    @abc.abstractmethod
    def track_call(self, name: str, description: str) -> AbstractMeasurerDelegate:
        raise NotImplementedError

    @abc.abstractmethod
    def export(self) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError
