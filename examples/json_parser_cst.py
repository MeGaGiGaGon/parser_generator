"""
A fully compliant json parser that produces a CST
(Concrete Syntax Tree, represents the full input in the output)
"""

from collections.abc import Sequence
from dataclasses import dataclass

from parser_generator import (
    ForwardRefParser,
    Parser,
    any_item,
    any_of,
    choose,
    empty,
    just,
)


@dataclass
class WS:
    value: str


ws = choose(any_of(" \r\n\t"), empty[str]().to("")).map(WS)


@dataclass
class Number:
    integer: str
    fraction: tuple[str, str] | None
    exponent: tuple[str, str, str] | None


sign = choose(any_of("+-"), empty[str]().to(""))

digit_rest: Parser[str, str] = (
    any_of("0123456789").then(ForwardRefParser(lambda: digit_rest)).map("".join)
)
digits = choose(just("0"), any_of("123456789").then(digit_rest).map("".join))

integer = choose(just("-"), empty[str]().to("")).then(digits).map("".join)
fraction = choose(just(".").then(digit_rest), empty[str]().to(None))
exponent = choose(
    any_of("eE").then(sign).unpack_then(digit_rest), empty[str]().to(None)
)

number = integer.then(fraction).unpack_then(exponent).star_map(Number)


@dataclass
class String:
    open: str
    chars: Sequence[tuple[str, str | tuple[str, int]] | str]
    close: str


hex_digit = any_of("0123456789abcdefABCDEF")
hexes = (
    hex_digit.then(hex_digit)
    .unpack_then(hex_digit)
    .unpack_then(hex_digit)
    .map("".join)
    .map(lambda x: int(x, 16))
)
escape = choose(any_of(R'"\/bfnrt'), just("u").then(hexes))
string_rest: Parser[
    str, tuple[Sequence[tuple[str, str | tuple[str, int]] | str], str]
] = choose(
    just('"').map(lambda x: (list[tuple[str, str | tuple[str, int]] | str](), x)),
    choose(just("\\").then(escape), any_item[str]())
    .then(ForwardRefParser(lambda: string_rest))
    .map(lambda x: ([x[0], *x[1][0]], x[1][1])),
)
string = just('"').then_unpack(string_rest).star_map(String)


@dataclass
class JSONObject:
    open: str
    ws: WS


print(string(r'"abcdef\n\r\t\\\"\ua12F"', 0))
