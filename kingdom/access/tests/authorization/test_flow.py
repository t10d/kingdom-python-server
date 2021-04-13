from kingdom.access.authentication.types import encode_jwt
from kingdom.access.authorization.flow import AuthFlow
from kingdom.access.tests.authorization.test_interface import default_user


"""
Problem:
    Given an incoming JWT token, authentication flow is responsible for:

    1. Verifying (and decoding) whther a JWT is valid.
    2. Return whether a user can perform a command
        > Cancel or not flow.
    3. Return which instances of a resource a subject can see
        > A list of resources-scope
"""


def create_valid_jwt() -> bytes, User:
    user = default_user()
    jwt, err = encode_jwt(user)
    return jwt
