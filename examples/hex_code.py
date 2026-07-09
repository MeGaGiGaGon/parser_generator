from dataclasses import dataclass
from parser_generator import any_of, Parser, just_seq


@dataclass
class HexCode:
    red: int
    green: int
    blue: int
    alpha: int = 255

hex_code_parser: Parser[str, HexCode] = (
    just_seq("0x")
    .ignore_then(
        any_of("0123456789abcdefABCDEF")
        .repeated(2)
        .map_ok("".join)
        .map_ok(lambda x: int(x, 16))
        .repeated(3, 4)
    )
    .map_ok(lambda x: HexCode(*x))
)
