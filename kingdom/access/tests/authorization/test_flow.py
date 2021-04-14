from kingdom.access.authentication.types import (
    AccessRequest,
    Permission,
    Resource,
    encode_jwt,
)
from kingdom.access.authorization.flow import AuthFlow
from kingdom.access.tests.authorization.test_interface import (
    gen_default_user,
    gen_invalid_token,
)

"""
Problem:
    Given an incoming JWT token, authentication flow is responsible for:

    1. Verifying (and decoding) whther a JWT is valid.
    2. Return whether a user can perform a command
        > Cancel or not flow.
    3. Return which instances of a resource a subject can see
        > A list of resources-scope
"""

JWT = bytes


def gen_valid_jwt() -> JWT:
    user = gen_default_user()
    jwt, err = encode_jwt(user)
    return jwt if jwt else b""


class TestHappyPath:
    def test_known_user_is_authenticated(self):
        access_request = AccessRequest(
            operation=Permission.READ,
            resource=Resource("Coupon"),
            selector="7fb4",
        )
        jwt = gen_valid_jwt()

        flow = AuthFlow(jwt, access_request)
        flow.authenticate()
        assert flow.is_authenticated

    def test_known_user_is_authenticated_and_authorized_to_read(self):
        access_request = AccessRequest(
            operation=Permission.READ,
            resource=Resource("Coupon"),
            selector="7fb4",
        )
        jwt = gen_valid_jwt()

        flow = AuthFlow(jwt, access_request)
        flow.authenticate()
        assert flow.is_authenticated

        flow.authorize()
        assert flow.is_authorized

        assert flow.scope() == ["7fb4", "49f3"]

    def test_known_user_is_authenticated_and_authorized_to_write(self):
        access_request = AccessRequest(
            operation=Permission.UPDATE,
            resource=Resource("User"),
            selector="ffff",
        )
        jwt = gen_valid_jwt()

        flow = AuthFlow(jwt, access_request)
        flow.authenticate()
        assert flow.is_authenticated

        flow.authorize()
        assert flow.is_authorized

        assert flow.scope() == ["ffff"]


class TestUnhappyPath:
    def test_unknown_user_is_not_authenticated(self):
        access_request = AccessRequest(
            operation=Permission.READ,
            resource=Resource("Coupon"),
            selector="7fb4",
        )
        jwt = gen_invalid_token()

        flow = AuthFlow(jwt, access_request)
        flow.authenticate()

        assert flow.is_authenticated is False

    def test_subject_has_no_permission_to_read(self):
        access_request = AccessRequest(
            operation=Permission.READ,
            resource=Resource("Wallet"),
            selector="*",
        )
        jwt = gen_valid_jwt()

        flow = AuthFlow(jwt, access_request)
        flow.authenticate()
        assert flow.is_authenticated

        flow.authorize()
        assert flow.is_authorized

        # permission to read nothing
        assert flow.scope() == []

    def test_subject_has_no_permission_to_write(self):
        access_request = AccessRequest(
            operation=Permission.CREATE,
            resource=Resource("Wallet"),
            selector="*",
        )
        jwt = gen_valid_jwt()

        flow = AuthFlow(jwt, access_request)
        flow.authenticate()
        assert flow.is_authenticated

        flow.authorize()
        assert flow.is_authorized is False

        assert flow.scope() == []

    def test_subject_has_no_permission_to_write_2(self):
        access_request = AccessRequest(
            operation=Permission.UPDATE,
            resource=Resource("User"),
            selector="4ff3",
        )
        jwt = gen_valid_jwt()

        flow = AuthFlow(jwt, access_request)
        flow.authenticate()
        assert flow.is_authenticated

        flow.authorize()
        assert flow.is_authorized is False

        assert flow.scope() == []
