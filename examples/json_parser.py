from collections.abc import Sequence
import sys
from pathlib import Path

sys.path += [str(Path(__file__).parent.parent)]
from parser_generator import (
    Err,
    Ok,
    Parser,
    ParserResult,
    any_of,
    ForwardRefParser,
    choice,
    just,
    simple_parser,
    just_seq,
)


ws: Parser[str, str] = any_of(" \n\r\t").err_to_ok("")

digit: Parser[str, str] = any_of("0123456789")
digits: Parser[str, str] = digit.repeated(1, None).map_ok("".join)
fraction: Parser[str, str] = just(".").then(digits).map_ok("".join).err_to_ok("")
sign: Parser[str, str] = any_of("+-").err_to_ok("")
exponent: Parser[str, str] = (
    any_of("eE").then(sign).then(digits).flatten().map_ok("".join).err_to_ok("")
)
non_leading_zero_digits: Parser[str, str] = (
    any_of("123456789").then(digit.repeated(0, None).map_ok("".join)).map_ok("".join)
)
integer: Parser[str, str] = (
    just("-").err_to_ok("").then(non_leading_zero_digits).map_ok("".join)
)

number_parser: Parser[str, float] = (
    integer.then(fraction).then(exponent).flatten().map_ok("".join).map_ok(float)
)

hex: Parser[str, int] = any_of("0123456789abcdefABCDEF").map_ok(lambda x: int(x, 16))
hex_char: Parser[str, str] = (
    hex.repeated(4, 4)
    .map_ok(lambda x: sum(v * 16**i for v, i in enumerate(x)))
    .map_ok(chr)
)
escape: Parser[str, str] = just("\\").ignore_then(
    choice(
        (any_of('"\\/'), any_of('"\\/')),
        (just("b"), just("b").ok_to("\b")),
        (just("f"), just("f").ok_to("\f")),
        (just("n"), just("n").ok_to("\n")),
        (just("r"), just("r").ok_to("\r")),
        (just("t"), just("t").ok_to("\t")),
        (just("u"), just("u").ignore_then(hex_char)),
    )
)


@simple_parser
def character(input: Sequence[str], index: int) -> ParserResult[str]:
    if index >= len(input) or input[index] == '"':
        return Err()
    match escape(input, index):
        case Ok() as ok:
            return ok
        case Err():
            if input[index] != "\\" and 0x0020 <= ord(input[index]) <= 0x10FFFF:
                return Ok((index + 1, input[index]))
            else:
                return Err()


string_parser: Parser[str, str] = (
    just('"')
    .ignore_then(character.repeated(0, None).map_ok("".join))
    .then_ignore(just('"'))
)

type Value = dict[str, Value] | list[Value] | str | float | bool | None

value_parser: Parser[str, Value] = ForwardRefParser(
    lambda: choice(
        (just("{"), object_parser),
        (just("["),  array_parser),
        (just('"'), string_parser),
        (integer, number_parser),
        (just_seq("true"), just_seq("true").ok_to(True)),
        (just_seq("false"), just_seq("false").ok_to(False)),
        (just_seq("null"), just_seq("null").ok_to(None)),
    )
)

element: Parser[str, Value] = ws.ignore_then(value_parser).then_ignore(ws)

object_member: Parser[str, tuple[str, Value]] = (
    ws.ignore_then(string_parser).then_ignore(ws).then_ignore(just(":")).then(element)
)
object_parser: Parser[str, dict[str, Value]] = (
    just("{")
    .ignore_then(
        choice(
            (ws.then(just('"')), object_member.separated_repeated(just(","), 1, None, False)),
            (ws, ws.ok_to(())),
        )
    )
    .then_ignore(just("}"))
    .map_ok(dict)
)

array_parser: Parser[str, list[Value]] = (
    just("[")
    .ignore_then(
        choice(
            (ws.then(just('"')), element.separated_repeated(just(","), 1, None, False)),
            (ws, ws.ok_to(())),
        )
    )
    .then_ignore(just("]"))
    .map_ok(list)
)


def json_parser(input: str) -> Value:
    match element(input, 0):
        case Ok((index, value)):
            if index != len(input):
                raise ValueError("Invalid json")
            return value
        case Err():
            raise ValueError("Invalid json")


def assert_eq(left: object, right: object):
    if left != right:
        raise AssertionError(f"Value {left} was not equal to {right}")


assert_eq(json_parser('{"a": -1.5e2}'), {"a": -1.5e2})
assert_eq(json_parser("[1, 2]"), [1, 2])
assert_eq(
    json_parser('{"1": [{"2": [null, true, false]}]}'),
    {"1": [{"2": [None, True, False]}]},
)
