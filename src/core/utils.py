import functools
import inspect
import logging
import unicodedata
from datetime import date, datetime
from typing import Callable, Dict, Any, Iterable, Optional, Set, List
from rapidfuzz.utils import default_process

logger = logging.getLogger("__utils__")


def inject_dependencies(
    handler: Callable, dependencies: Dict[str, Any]
) -> Callable:
    """
    Inspects a handler function to figure out its arguments and returns the
    same handler with its arguments already set given a dependencies
    mapping

    TODO: This could be done also by using functools.partial
    """
    params = inspect.signature(handler).parameters
    set_dependencies = {
        param: dependency
        for param, dependency in dependencies.items()
        if param in params
    }
    return lambda message: handler(message, **set_dependencies)


def group_rows(
    rows: List[Dict],
    identifier: str,
    group_key: str,
    keys_to_flat: Set,
    keys_to_group: Set,
) -> List[Dict]:
    """A list of rows that have flattened base-levels and grouped values like
    >>> _rows = [
    >>>    {'id': 0x3d, 'name': 'bob', 'product': 32},
    >>>    {'id': 0x3d, 'name': 'bob', 'product': 33}
    >>> ]
    >>> group_rows(_rows, 'id', 'all_products', {'bob', 'name'}, {'product'})
    >>> {
    >>>     'id': 0x3d,
    >>>     'name': 'bob',
    >>>     'all_products': [{'product': 32},{'product': 33}]
    >>> }
    """

    def filterkeys(row: Dict, keys: Set) -> Dict:
        """Filters dict to only specified keys"""
        return {k: v for k, v in row.items() if k in keys}

    new_group_item = lambda row: filterkeys(row, keys_to_group)  # noqa:E731

    partial: Dict[str, Dict] = {}
    for row in rows:
        id = row[identifier]
        if id in partial:
            partial[id][group_key].append(new_group_item(row))
        else:
            new_row = filterkeys(row, keys_to_flat)
            new_row[group_key] = [new_group_item(row)]
            partial[id] = new_row
    return [{**rows} for rows in partial.values()]


def group_by(rows: List[Dict], identifier: str) -> Dict[str, List]:
    grouped = {}
    for r in rows:
        id = r.pop(identifier)
        if id in grouped:
            grouped[id].append(r)
            continue
        grouped[id] = [r]
    return grouped


def ifilter(
    elements: Iterable[Any],
    match_rule: Callable,
    default: Optional[Any] = None,
):
    try:
        return next(filter(match_rule, elements))
    except StopIteration:
        return default


def create_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        p_info = kwargs.pop("pagination_info") or dict(offset=0, limit=10)
        rows = func(*args, **kwargs, pagination_info=p_info)
        limit, offset = p_info["limit"], p_info["offset"]
        elements_count = 0
        if rows:
            try:
                elements_count = rows[0]["elements_count"]
            except Exception as ex:
                logger.exception(str(ex))
                raise AttributeError("Query is missing elements_count")

        if limit is None:
            limit = elements_count
        start_offset = offset
        end_offset = (
            elements_count
            if offset + limit > elements_count
            else offset + limit
        )

        return {
            "elements": rows,
            "elements_count": elements_count,
            "page_info": {
                "has_next_page": not end_offset == elements_count,
                "start_offset": start_offset,
                "end_offset": end_offset,
            },
        }

    return wrapper


def normalize_string(s: str) -> str:
    """Receives a string and apply transformations to normalize it making
    fuzzy match easier
    >>> normalize_string("São Paulo - Capital, SP")
    "sao paulo capital sp"
    """
    s = default_process(s)
    normalized = (
        unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode()
    )
    return " ".join(normalized.split())


def normalize_id_number(s: str) -> str:
    s = normalize_string(s)
    return "".join(s.split())


def validate_id(
    number: str, expected_length: int, mult_table_fun: Callable
) -> bool:
    """Validates both CPF and CNPJ based on expected_length"""
    if not len(number) == expected_length:
        raise ValueError("number has invalid length")

    delimiter: int = expected_length - 2
    word, digits = (number[:delimiter], number[delimiter:])
    word_numeric: List[int] = [int(d) for d in word]

    for (i, digit) in enumerate(digits):
        calculated_digit = create_digit(word_numeric, mult_table_fun)
        if not calculated_digit == int(digit):
            raise ValueError(
                f"Digit {i+1}: Expected {digit}, got {calculated_digit}"
            )
        word_numeric += [calculated_digit]
    return True


def reversed_array(start: int, N: int) -> List[int]:
    """Reverses an array of integers ranging from start -> start + N"""
    return list(reversed(range(start, start + N)))


def mult_table_cpf(word_length: int) -> List[int]:
    """Multiplication table for CPF's modulus 11 calculation

    >>> mult_table_cpf(9)
    >>> [9, 8, 7, 6, 5, 4, 3, 2]
    """
    return reversed_array(start=2, N=word_length)


def mult_table_cnpj(word_length: int) -> List[int]:
    """Multiplication table for CNPJ's modulus 11 calculation

    >>> mult_table_cnpj(12)
    >>> [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    """
    return mult_table_cpf(word_length - 8) + mult_table_cpf(8)


def create_digit(word: List[int], mult_table: Callable) -> int:
    """Given a word, calculates its digit by performing modulus 11 calc

    >>> w = [2, 3, 4, 9, 0, 3, 5, 1]
    >>> create_digit(w, mask_gen)
    0"""
    word_sum = sum([a * b for a, b in zip(word, mult_table(len(word)))])
    rest = word_sum % 11
    return 0 if rest < 2 else (11 - rest)


def validate_cpf(cpf: str) -> bool:
    try:
        return validate_id(cpf, 11, mult_table_cpf)
    except ValueError:
        return False


def validate_cnpj(cnpj: str) -> bool:
    try:
        return validate_id(cnpj, 14, mult_table_cnpj)
    except ValueError:
        return False


def validate_cnpj_or_cpf(id_number: str) -> bool:
    return any(
        [
            len(id_number) == 11 and validate_cpf(id_number),
            len(id_number) == 14 and validate_cnpj(id_number),
        ]
    )


def get_date(dt: Any, date_format: str) -> date:
    if isinstance(dt, datetime):
        return dt.date()
    if isinstance(dt, date):
        return dt
    if type(dt) is str:
        return datetime.strptime(dt, date_format).date()
    raise ValueError("Date must be a string, datetime or date.")
