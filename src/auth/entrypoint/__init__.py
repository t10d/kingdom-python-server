from typing import Optional

from craftship.auth.services import unit_of_work
from craftship.auth.adapters.email_sender import EmailSender

uow: Optional[unit_of_work.AuthSqlAlchemyUnitOfWork] = None
email_sender: Optional[EmailSender] = None
