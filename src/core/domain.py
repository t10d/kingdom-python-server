from dataclasses import dataclass
from datetime import datetime


class Entity:
    pass


class ValueObject:
    pass


class Aggregate:
    _events: list
    _version: int

    def __init__(self):
        self._events = []
        self._version = 0


class Message:
    kind: str
    raised_at: datetime

    def __init__(self):
        self.type = "GenericMessage"
        self.kind = self.__class__.__name__
        self.raised_at = datetime.now()
        self.delay = 0

    def __str__(self) -> str:
        return str(self.__repr__())

    def __repr__(self) -> str:
        return (
            f"<{self.type} {self.kind} raised at "
            f"{self.raised_at} and params: {self.__dict__}>"
        )


class Event(Message):
    def __init__(self):
        super().__init__()
        self.type = "Event"


class Command(Message):
    def __init__(self):
        super().__init__()
        self.type = "Command"
