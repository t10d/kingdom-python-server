import abc
from typing import List, Set

from sqlalchemy import orm


class AbstractEmailSender(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def send_email(
        self,
        email_to: str,
        subject: str,
        template: str,
    ) -> int:
        raise NotImplementedError
