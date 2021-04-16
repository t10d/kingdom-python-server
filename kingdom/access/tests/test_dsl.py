from kingdom.access.dsl import (
    conditionals_split,
    parse_expression,
    parse_identifier,
    parse_identifier_reference,
    parse_operator,
    parse_reference,
    parse_selector,
)


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


def test_parse_operator():
    input = [
        "== 'd8f7s9d8f7'",  # valid
        "== '8dfs8d7f9'",  # valid
        "== ''",  # valid
        "== \"'21f90912'\"  ",  # invalid
        "== '21f90912'  ",  # valid
        "= '*' ",  # invalid
        '< "ddx"',  # invalid
        "  < '3030fk30'",  # valid
        " >    ''",  # valid
        " >>    ''",  # invalid
        "=== '*'",  # invalid
        ">= '2fd04'",  # valid
        "!= '*'",  # valid
        " + '*'",  # invalid
        "-- 'd'",  # invalid
        "/   'xxvc'",  # invalid
        "=+ '*'",  # invalid
        "=- '*'",  # invalid
    ]
    want = [
        ("==", "'d8f7s9d8f7'"),  # valid
        ("==", "'8dfs8d7f9'"),  # valid
        ("==", "''"),  # valid
        (False,),  # invalid
        ("==", "'21f90912'"),  # valid
        (False,),  # invalid
        (False,),  # invalid
        ("<", "'3030fk30'"),  # valid
        (">", "''"),  # valid
        (False,),  # valid
        (False,),  # invalid
        (">=", "'2fd04'"),  # valid
        ("!=", "'*'"),  # valid
        (False,),  # invalid
        (False,),  # invalid
        (False,),  # invalid
        (False,),  # invalid
        (False,),  # invalid
    ]
    got = [parse_operator(op) for op in input]
    assert got == want


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
