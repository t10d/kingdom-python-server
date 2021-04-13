from dataclasses import dataclass


@dataclass
class AuthFlow:
    JWT: bytes
