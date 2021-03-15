import os
import random
from faker import Faker


def read_graphql(path: str) -> str:
    fullpath = os.path.abspath(path)
    with open(fullpath) as f:
        lines = f.readlines()
    return "".join(lines)


def random_id_number_pj() -> str:
    digits = [d for d in range(0, 10)]
    return "".join([str(random.choice(digits)) for _ in range(14)])


def random_id_number_pf() -> str:
    digits = [d for d in range(0, 10)]
    return "".join([str(random.choice(digits)) for _ in range(11)])


def random_valid_cpf() -> str:
    cpf = [random.randint(0, 9) for x in range(9)]
    for _ in range(2):
        val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
        cpf.append(11 - val if val > 1 else 0)
    return "".join(str(n) for n in cpf)


def random_valid_cnpj() -> str:
    def calculate_special_digit(l):
        digit = 0
        for i, v in enumerate(l):
            digit += v * (i % 8 + 2)
        digit = 11 - digit % 11
        return digit if digit < 10 else 0

    cnpj = [1, 0, 0, 0] + [random.randint(0, 9) for x in range(8)]

    for _ in range(2):
        cnpj = [calculate_special_digit(cnpj)] + cnpj

    cnpj = cnpj[::-1]
    return "".join(str(n) for n in cnpj)


def random_word():
    return Faker().word()


def random_name() -> str:
    return Faker().name()


def random_phone():
    digits = [d for d in range(0, 10)]
    return "".join([str(random.choice(digits)) for _ in range(11)])


def random_email() -> str:
    return random.choice(
        [
            Faker().ascii_company_email,
            Faker().ascii_email,
            Faker().ascii_free_email,
            Faker().ascii_safe_email,
        ]
    )()


def random_int() -> int:
    return Faker().random_int()
