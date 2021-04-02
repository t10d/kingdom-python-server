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
        "resource.id",
        "resourceeee.id",
        "r esource.id",
        "resource .id",
        " r esource.id",
        "resource..id",
    ]
    want = [
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
    identifier = ""
    for idx, token in enumerate(expression):
        if token.isidentifier():
            identifier += token
        else:
            if token == ".":
                return identifier, expression[idx:]
            return (False,)


def test_parse_reference():
    input = [
        ".id",
        " .id",
        " id",
        ".id  ",
        "..id..",
        ".nope",
        ".that!",
        "[index]",
        ".fine0",
        ".name@",
        ".na me",
        ".name",
    ]

    want = [
        "id",
        False,
        False,
        False,
        False,
        "nope",
        False,
        False,
        False,
        False,
        False,
        "name"
    ]

    got = [parse_reference(ref) for ref in input]
    assert got == want


def parse_reference(reference_expr):
    reference = ""
    for idx, token in enumerate(reference_expr):
        if idx == 0:
            if token != ".":
                return False
            continue

        if token.isidentifier():
            reference += token
        else:
            return False
    return reference


def test_parse_identifier_reference():
    input = [
        "resource.id",
        "resourceeee.id",
        "r esource.id",
        "resource .id",
        " r esource.id",
        "resource.id",
        "resource.name",
        "resource.na me",
        "resource.name!",
        "rsrc!name",
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
        False,
        False
    ]
    got = [parse_identifier_reference(expr) for expr in input]
    assert got == want


def parse_identifier_reference(expression):
    identifier, *reference_expr = parse_identifier(expression)
    if identifier is False:
        return False
    reference = parse_reference(*reference_expr)
    if reference is False:
        return False

    return (identifier.upper(), reference.upper())


def test_parse_operator():
    input = [
        "==",
        " ==",
        "==  ",
        "=",
        "<",
        "  <",
        " > ",
        "===",
        ">=",
        "!=",
        " + ",
        "--",
        "/",
        "=+",
        "=-",
    ]
    want = [
        "==",
        "==",
        "==",
        False,
        "<",
        "<",
        ">",
        False,
        ">=",
        "<=",
        "!=",
        False,
        False,
        False,
        False,
        False,
    ]
    got = [parse_operator(op) for op in input]
    assert got == want


def parse_operator(operator_expr):
    VALID_OPS = {"==", ">", "<", ">=", "<=", "!="}
    VALID_TOKEN = {token for operator in VALID_OPS for token in operator}

    operator = ""
    found = False
    for idx, token in enumerate(operator_expr):
        if token in VALID_TOKEN:
            # we need to properly *walk* precisely the number of characters 
            # to find a valid operator
            if operator in VALID_OPS and not found:
                # first time found an operator
                found = True
            if operator in VALID_OPS and found:
                # we are dealing with ===, !==, >>, etc
                return False

            # here we are with 1-token 
            operator += token
        else:
            if token.isspace():
                continue
            else:
                return False

    if operator in VALID_OPS:
        return operator
    return False

def tst_parse_valid_conditional():
    input = [
        "resource.id == 128f12334hjg"
        "resource.id    ==  128f12334hjg"
        "resource.id ==12839712893791823",
        "resource.id== 12839712893791823",
        "resource.id==128f12334hjg",
        "resource.id==*",
        "resource.id ==*",
        "resource.id== *"
    ]

    want = [
     ("RESOURCE", "ID", "==", "128f12334hjg"),
     ("RESOURCE", "ID", "==", "128f12334hjg"),
     ("RESOURCE", "ID", "==", "12839712893791823"),
     ("RESOURCE", "ID", "==", "12839712893791823"),
     ("RESOURCE", "ID", "==", "128f12334hjg"),
     ("RESOURCE", "ID", "==", "*"),
     ("RESOURCE", "ID", "==", "*"),
     ("RESOURCE", "ID", "==", "*"),
    ]

    got = [parse_condition(cond) for cond in input]

    assert got == want


