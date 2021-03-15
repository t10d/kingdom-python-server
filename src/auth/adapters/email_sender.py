import emails
import logging

from src.core.ports.email_sender import AbstractEmailSender
from src.auth import config


class EmailSender(AbstractEmailSender):
    def __init__(self):
        self.smtp_options = {
            "host": config.get_smtp_host(),
            "port": config.get_smtp_port(),
            "user": config.get_smtp_user(),
            "password": config.get_smtp_pwd(),
            "tls": True,
        }

    def send_email(
        self,
        email_to: str,
        subject: str,
        template: str,
    ) -> int:
        message = emails.Message(
            subject=subject,
            html=template,
            mail_from=(config.get_email_name(), config.get_smtp_user()),
        )
        logging.info(f"Sending email to {email_to} with subject: {subject}")
        response = message.send(to=email_to, smtp=self.smtp_options)
        logging.info(f"Email sent, service response: {response}")
        return response.status_code
