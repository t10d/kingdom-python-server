from kingdom.access.authentication.types import (
    JWT_ALGORITHM,
    RANDOM_KEY,
    Conditional,
    JWTDecodedPayload,
    MaybeBytes,
    MaybePayload,
    Permission,
    Policy,
    Resource,
    Role,
    User,
    decode_jwt,
    encode_jwt,
    encode_user_payload,
    encode_user_policies,
)


"""
Problems:

1. We have a user and we want to issue a JWT on his behalf.
2. We have a JWT and want to parse a JWT on his behalf
"""

"""Problem 1:
1. We need to have the mininum set of User-Role-Policy domain defined.
"""


def default_user() -> User:
    product_read = Policy(
        resource=Resource("Product"),
        permissions=(Permission.READ,),
        conditionals=[Conditional("resource.id", "*"), ],
    )
    specific_coupon = Policy(
        resource=Resource("Coupon"),
        permissions=(Permission.READ,),
        conditionals=[
            Conditional("resource.id", "7fb4"),
            Conditional("resource.id", "49f3"),
        ],
    )
    role = Role(
        name="default consumer", policies=[product_read, specific_coupon]
    )
    user = User(access_key="abc4f", roles=[role])
    return user


def test_successful_encoding_and_decoding():
    user = default_user()
    user_policies = encode_user_policies(user)

    jwt, err_encode = encode_jwt(user)
    assert err_encode is None

    decoded_jwt, err_decode = decode_jwt(jwt)
    assert err_decode is None

    assert user_policies == decoded_jwt["roles"]


def test_unsuccessful_decoding():
    from string import ascii_letters
    from random import randint

    def token_part():
        return "".join(ascii_letters[randint(0, 50)] for _ in range(1, 64))

    token = ".".join(token_part() for _ in range(3))
    _, err_decode = decode_jwt(token.encode())
    assert isinstance(err_decode, Exception)
