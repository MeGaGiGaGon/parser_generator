from dataclasses import dataclass

from parser_generator import any_of, choose, empty, just_seq


@dataclass
class HexCode:
    red: int
    green: int
    blue: int
    alpha: int


hex_digit = any_of("0123456789abcdefABCDEF")
color_hex = hex_digit.then(hex_digit).map("".join).map(lambda x: int(x, 16))

hex_code_parser = (
    just_seq("0x")
    .ignore_then(
        color_hex.then(color_hex)
        .unpack_then(color_hex)
        .unpack_then(choose(color_hex, empty[str]().to(255)))
    )
    .star_map(HexCode)
)

# Test implementation

import unittest


class TestParser(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(hex_code_parser("0x000000", 0), (HexCode(0, 0, 0, 255), 8))
        self.assertEqual(hex_code_parser("0x0000007F", 0), (HexCode(0, 0, 0, 0x7F), 10))
        self.assertEqual(
            hex_code_parser("0x7F7F7F7F", 0), (HexCode(0x7F, 0x7F, 0x7F, 0x7F), 10)
        )
        self.assertEqual(
            hex_code_parser("0xabcdef", 0), (HexCode(0xAB, 0xCD, 0xEF, 255), 8)
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:  # noqa: PLR2004
        print(hex_code_parser(sys.argv[1], 0))  # noqa: T201
    else:
        _ = unittest.main()
