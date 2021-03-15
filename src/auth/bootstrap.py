from src.core.ports.unit_of_work import AbstractUnitOfWork
from src.core.ports.email_sender import AbstractEmailSender
from src.auth.services import unit_of_work
from src.auth.adapters import email_sender


def create(
    uow: AbstractUnitOfWork = unit_of_work.AuthSqlAlchemyUnitOfWork(),
    email_sender: AbstractEmailSender = email_sender.EmailSender(),
    **kwargs
):
    return uow, email_sender
