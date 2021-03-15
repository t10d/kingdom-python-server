from craftship.core.ports.unit_of_work import AbstractUnitOfWork
from craftship.core.ports.email_sender import AbstractEmailSender
from craftship.auth.services import unit_of_work
from craftship.auth.adapters import email_sender


def create(
    uow: AbstractUnitOfWork = unit_of_work.AuthSqlAlchemyUnitOfWork(),
    email_sender: AbstractEmailSender = email_sender.EmailSender(),
    **kwargs
):
    return uow, email_sender
