# test_authorization.py
""""
dsl.py

 SPECIFICATION of Conditionals:

 Vocabulary. These contains current implementation expected limitations and
 simplifications:
   primary     ::= "resource"
   identifier  ::= "id"
   selector    ::= "*" | string
   attrref     ::= primary "." identifier
   or_expr     ::= "||"
   compr_op    ::= "=="
   cond        ::= attrref compr_op selector
   conds       ::= (cond or_expr)*

 There are two available selectors:
   1. All instances:        "*"
   2. Individual instances: "<uuid>"

 There are some conditions to selectors:
   1. All selector must **always** be alone.

OBS.: This is in WIP and should be thoroughly simplified & documented.
"""

import string
from typing import List

TOKEN_ALL = "*"
VALID_OPS = {"==", ">", "<", ">=", "<=", "!="}
VALID_OPS_TOKEN = {token for operator in VALID_OPS for token in operator}


def conditionals_split(sequence: str):
    expressions = sequence.split("||")
    if "" in expressions or " " in expressions:
        # meaning that we had a loose OR
        return False

    parsed_expr = [expression.strip() for expression in expressions]
    for expr in parsed_expr:
        for char in expr:
            if char.isspace():
                # illegal whitespaces
                return False

            if char in set(string.punctuation):
                # illegal characteres
                return False

    return tuple(parsed_expr)


def parse_identifier(expression):
    # since it's the beginning, we can strip this, to avoid overly
    # complicated iterations :-)
    expression = expression.strip()
    identifier = ""
    for idx, token in enumerate(expression):
        if token.isidentifier():
            identifier += token
        else:
            if token == "." and len(identifier) > 0:
                return identifier, expression[idx:]
            return (False,)


def parse_reference(reference_expr):
    reference = ""
    parsing_idx = -1

    # first we try to read all valid tokens after "." and before a valid
    # operator
    for idx, token in enumerate(reference_expr):
        if idx == 0:
            # first token **must** be a ".", no other one allowed
            if token != ".":
                return (False,)
            parsing_idx = idx
            continue

        if token.isspace() or token in VALID_OPS_TOKEN:
            # we have found our potential reference
            parsing_idx = idx
            break

        if token.isidentifier():
            reference += token
        else:
            return (False,)

    # check for illegality on the rest of the expression
    # meaning we must only accept white spaces between end of ref and operator
    rest = reference_expr[parsing_idx:]
    for idx, token in enumerate(rest):
        if token in VALID_OPS_TOKEN:
            return (reference, rest[idx:])

        if token.isspace():
            # the only acceptable token between a ref and operator
            continue
        else:
            return (False,)


def parse_identifier_reference(expression):
    identifier, *reference_expr = parse_identifier(expression)
    if identifier is False:
        return False
    reference, *operator_expr = parse_reference(*reference_expr)
    if reference is False:
        return False

    return (identifier.upper(), reference.upper())


def parse_operator(operator_expr):
    operator_expr = operator_expr.strip()  # just to make sure

    operator = ""
    parsing_idx = -1
    # First we parse a known operator.
    for idx, token in enumerate(operator_expr):
        if token in VALID_OPS_TOKEN:
            # the only valid thing that is being parsed
            operator += token
        else:
            parsing_idx = idx
            break

    # Then we check if the rest is OK.
    rest = operator_expr[parsing_idx:]
    for idx, token in enumerate(rest):
        if token == "'":
            # valid stopping point
            if operator in VALID_OPS:
                return (operator, rest[idx:])
            # invalid operator
            return (False,)

        if token.isspace():
            continue
        else:
            # illegal characteres
            return (False,)


def parse_selector(selector_expr):
    selector_expr = selector_expr.strip()
    selector = ""
    parsing_idx = -1

    def isselector(token):
        return token.isnumeric() or token.isidentifier() or token == TOKEN_ALL

    # First we try to find a selector.
    for idx, token in enumerate(selector_expr):
        if idx == 0:
            # first token
            if token != "'":
                return (False,)
            continue

        if token == "'":
            parsing_idx = idx + 1
            break

        if isselector(token):
            selector += token
        else:
            return (False,)

    # Edge case: are we dealig with an *?
    if TOKEN_ALL in selector and selector != TOKEN_ALL:
        # plain comparison
        return (False,)

    rest = selector_expr[parsing_idx + 1:]
    if len(rest) > 0 or len(selector) == 0:
        # we shouldn't have anything left
        return (False,)
    return (selector,)


def parse_expression(expr):
    identifier, *reference_expr = parse_identifier(expr)
    if identifier is False:
        return False
    reference, *operator_expr = parse_reference(*reference_expr)
    if reference is False:
        return False
    operator, *selector_expr = parse_operator(*operator_expr)
    if operator is False:
        return False
    selector, *end = parse_selector(*selector_expr)
    if selector is False:
        return False
    return (identifier, reference, operator, selector)
