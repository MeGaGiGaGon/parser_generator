from dataclasses import dataclass
from parser_generator import *


@dataclass
class HexCode:
    red: int
    green: int
    blue: int
    alpha: int


hex_digit = any_of("0123456789abcdefABCDEF")
color_hex = hex_digit.then(hex_digit).map("".join).map(lambda x: int(x, 16))

hex_code_parser: Parser[str, HexCode] = (
    just_seq("0x")
    .ignore_then(
        color_hex.then(color_hex)
        .unpack_then(color_hex)
        .unpack_then(choose(color_hex, empty().to(255)))
    )
    .star_map(HexCode)
)
