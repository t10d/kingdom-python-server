from tests.auth import helpers
from src.auth.adapters import email_sender


def test_send_email():
    sender = email_sender.EmailSender()
    response = sender.send_email(
        email_to=helpers.TEST_USER_EMAIL,
        subject=helpers.random_word(),
        template=helpers.random_word(),
    )
    assert response == 250
