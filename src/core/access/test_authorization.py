# test_authorization.py

# Requirements:
# A user tries to access a given resource. We need to check if it has enough 
# access running a policy check under a context of available data.
# 
# User policies are resolved through its associated Roles.
#
# Relationships:
#   User   1 .. N Role
#   Role   1 .. N Policy
#   Policy 1 .. 1 Operation 
#   Policy 1 .. 1 Resource
#   Policy 1 .. N Where Clauses
#
# Policy:
#   - operation:     [READ, CREATE, UPDATE, DELETE]
#   - resource:      [ACCOUNT]
#   - conditionals:  [resource.id = *] 
#
# INTERPRETATION of a Policy: 
#
# A role {r} 
# is allowed to do {operation}
# on all instances of {resource}
# that satisfies {conditional[0]} or {conditional[1]} or {conditional[N-1]}
#
# SPECIFICATION of Conditionals: 
# 
# Vocabulary. These contains current implementation expected limitations and
# simplifications: 
#   primary     ::= "resource"
#   identifier  ::= "id"
#   selector    ::= "*" | string
#   attrref     ::= primary "." identifier 
#   or_expr     ::= "||"
#   compr_op    ::= "=="
#   cond        ::= attrref compr_op selector
#   conds       ::= (cond or_expr)*
#
# There are two available selectors:
#   1. All instances:        "*"    
#   2. Individual instances: "<uuid>"
#
# There are some conditions to selectors:
#   1. All selector must **always** be alone.
#

import string
from typing import List


valid_conditionals = [
    "resource.id == 128f12334hjg || resource.id == 12839712893791823",
    "resource.id==128f12334hjg||resource.id==12839712893791823",
    "resource.id==*",
    "resource.id ==*",
    "resource.id== *"
]

simplified_conditionals = {
    # This meanings that list[0] should be translated to list[1]
    "selector conditional": [
        "resource.id==*||resource.id==8123798fcd89||resource.id==8197498127",
        "resource.id == *"
    ]
}

invalid_conditionals = [
    "resource.id == 9284234 ||",
    "resource.id = 1238912fd || resource.id ==182789123",
    "resource.id 12381723",
    "resource.id == 1928309182 resource.id = 12930918",
    "resource.id == 81927398123 || resource.id = 9128398",
    "resource .id == 12893789123",
    "resource. id == 89071239",
    "resource.id == 182937 12893 827381723 || resource.id == 1892 9283"
    "resource.id == 18297389f|resource.id==1827398f",
    "resouce.id == 1283971283ff || subject.id == 1891273987123",
    "resource.created_at == 2319833012707 || resource.id == faf76bc7",
    "resource.id == 8129370192ff || resource.id == 8123091283908",
    "resource.id!=291f767d8bc"
]


def test_conditionals_split():
    input = [
        "expr || newexpr",
        "expr||newexpr",
        "  expr || newexpr    ",
        "expr|newexpr",
        "expr   || newexpr||neewexpr||",
        "ex pr   || new expr ||  ",
        "  expr ||| newexpr    ",
        "  expr|||newexpr    ",
    ]

    want = [
        ("expr", "newexpr"),
        ("expr", "newexpr"),
        ("expr", "newexpr"),
        False,
        False,
        False,
        False,
        False,
    ]

    got = [conditionals_split(sequence) for sequence in input]
    assert got == want


def conditionals_split(sequence: str):
    expressions = sequence.split("||")
    if "" in expressions:
        # meaning that we had a loose OR
        return False

    parsed_expr = [
        expression.strip() for expression in expressions
    ]
    for expr in parsed_expr:
        for char in expr:
            if char.isspace():
                # illegal whitespaces
                return False

            if char in set(string.punctuation):
                # illegal characteres
                return False

    return tuple(parsed_expr)


def test_parse_identifier():
    input = [
        ".id",
        "resource.id",
        "   resourceeee.id",
        "r es ource.id",
        "resource .id",
        " r esource.id",
        "resource..id",
    ]
    want = [
        (False,),
        ("resource", ".id"),
        ("resourceeee", ".id"),
        (False,),
        (False,),
        (False,),
        ("resource", "..id"),
    ]
    got = [parse_identifier(i) for i in input]
    assert got == want


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


def test_parse_reference():
    input = [
        ".",
        ".id==",
        " .id>",
        " id==",
        ".id   === ",
        "..id..",
        ".nope    =",
        ".that!=",
        "[index]>=",
        ".fine0  ==",
        ".name@ <=",
        ".n a m e ===",
        ".name >>",
    ]

    want = [
        (False,),
        ("id", "=="),
        (False,),
        (False,),
        ("id", "=== "),
        (False,),
        ("nope", "="),
        ("that", "!="),
        (False,),
        (False,),
        (False,),
        (False,),
        ("name", ">>"),
    ]

    got = [parse_reference(ref) for ref in input]
    assert got == want


VALID_OPS = {"==", ">", "<", ">=", "<=", "!="}
VALID_OPS_TOKEN = {token for operator in VALID_OPS for token in operator}


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


def test_parse_identifier_reference():
    input = [
        "resource.id==",
        "resourceeee.id>=",
        "r esource.id  ==",
        "resource .id <=",
        " r esource.id =",
        "resource.id  <<",
        "resource.name <=",
        "resource.na me !=",
        "resource.name ===",
        "rsrc!name ==",
    ]
    want = [
        ("RESOURCE", "ID"),
        ("RESOURCEEEE", "ID"),
        False,
        False,
        False,
        ("RESOURCE", "ID"),
        ("RESOURCE", "NAME"),
        False,
        ("RESOURCE", "NAME"),
        False,
    ]
    got = [parse_identifier_reference(expr) for expr in input]
    assert got == want


def parse_identifier_reference(expression):
    identifier, *reference_expr = parse_identifier(expression)
    if identifier is False:
        return False
    reference, *operator_expr = parse_reference(*reference_expr)
    if reference is False:
        return False

    return (identifier.upper(), reference.upper())


def test_parse_operator():
    input = [
        "== 'd8f7s9d8f7'",        # valid
        "== '8dfs8d7f9'",         # valid
        "== ''",                  # valid
        "== \"'21f90912'\"  ",    # invalid
        "== '21f90912'  ",        # valid
        "= '*' ",                 # invalid
        "< \"ddx\"",              # invalid
        "  < '3030fk30'",         # valid
        " >    ''",               # valid
        " >>    ''",              # invalid
        "=== '*'",                # invalid 
        ">= '2fd04'",             # valid
        "!= '*'",                 # valid
        " + '*'",                 # invalid
        "-- 'd'",                 # invalid
        "/   'xxvc'",             # invalid
        "=+ '*'",                 # invalid
        "=- '*'",                 # invalid
    ]
    want = [
        ("==", "'d8f7s9d8f7'"),   # valid
        ("==", "'8dfs8d7f9'"),    # valid
        ("==", "''"),             # valid
        (False,),                 # invalid
        ("==", "'21f90912'"),     # valid
        (False,),                 # invalid
        (False,),                 # invalid
        ("<", "'3030fk30'"),      # valid
        (">", "''"),              # valid
        (False,),                 # valid
        (False,),                 # invalid 
        (">=", "'2fd04'"),        # valid
        ("!=", "'*'"),            # valid
        (False,),                 # invalid
        (False,),                 # invalid
        (False,),                 # invalid
        (False,),                 # invalid
        (False,),                 # invalid
    ]
    got = [parse_operator(op) for op in input]
    assert got == want


def parse_operator(operator_expr):
    operator_expr = operator_expr.strip()  # just to make sure
    VALID_OPS = {"==", ">", "<", ">=", "<=", "!="}
    VALID_TOKEN = {token for operator in VALID_OPS for token in operator}

    operator = ""
    parsing_idx = -1
    for idx, token in enumerate(operator_expr):
        if token in VALID_TOKEN:
            # the only valid thing that is being parsed
            operator += token
        else:
            parsing_idx = idx
            break

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


def test_parse_valid_selector():
    input = [
        "   '128f12334hjg'",
        "   '128f12334hjg'",
        "'12839712893791823'",
        " '12839712893791823'",
        " '128f12334hjg'",
        "'*'",
        " '*'",
        " '**'",
        " '!'",
        "'12837891ff",
        "'123123'123123'",
        "''",
        "'fff\"dddsd'",
        "'''",
        "';1234234fgds00x;;",
        "'f5f65b65c!!'",
        "f4'dfadf7'",
    ]

    want = [
        ("128f12334hjg",),
        ("128f12334hjg",),
        ("12839712893791823",),
        ("12839712893791823",),
        ("128f12334hjg",),
        ("*",),
        ("*",),
        (False,),
        (False,),
        (False,),
        (False,),
        (False,),
        (False,),
        (False,),
        (False,),
        (False,),
        (False,),
    ]

    got = [parse_selector(cond) for cond in input]

    assert got == want


def parse_selector(selector_expr):
    ALL_TOKEN = "*"
    selector_expr = selector_expr.strip()
    selector = ""
    parsing_idx = -1

    def isselector(token):
        return (
            token.isnumeric()
            or token.isidentifier()
            or token == ALL_TOKEN
        )

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

    # are we dealig with an *?
    if ALL_TOKEN in selector and selector != '*':
        # plain comparison 
        return (False,)

    rest = selector_expr[parsing_idx + 1:]
    if len(rest) > 0 or len(selector) == 0:
        # we shouldn't have anything left 
        return (False,)
    return (selector,)


def test_parse_expressions():
    valid_input = [
        "resource.id=='d8s7f987sdf'",
        "resource.id == 'd8s7f987sdf'",
        "resource.id == '*'",
        "subject.salary > '1800'",
        "subject.salary <= '1800'",
        "some.name == 'ab9f8d0'",
    ]

    invalid_input = [
        "resource..id == '8d9f7a8f'",
        ".id == 'xxx'",
        "'resource'.id == '*'",
        "reso urce.id == '*'",
        "resource.id === '*'",
        "resource.id='dgv8bf'",
        "resource.id == \"*\"",
        "subject.salary > 1800",
    ]

    got = [parse_expression(expr) for expr in valid_input]
    want = [
        ("resource", "id", "==", "d8s7f987sdf"),
        ("resource", "id", "==", "d8s7f987sdf"),
        ("resource", "id", "==", "*"),
        ("subject", "salary", ">", "1800"),
        ("subject", "salary", "<=", "1800"),
        ("some", "name", "==", "ab9f8d0"),
    ]
    assert got == want

    got = [parse_expression(expr) for expr in invalid_input]
    want = [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    ]
    assert got == want


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

