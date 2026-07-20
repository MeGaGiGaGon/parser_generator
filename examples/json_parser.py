"""
Note: this uses a simplified json syntax to avoid having
to deal with the more fiddly bits
(no str escape codes and only plain integer numbers)
"""

from dataclasses import dataclass
from typing import Literal

from parser_generator import (
    ForwardRefParser,
    Parser,
    any_item,
    any_of,
    choose,
    empty,
    end_of_file,
    just,
    just_seq,
    start_of_file,
)


# Use a dataclass to stop type checkers failing
# on recursive typevar solving
@dataclass
class Element:
    value: dict[str, Element] | list[Element] | int | str | bool | None


ws = any_of(" \r\n\t").repeated(empty[str]().to("")).map(lambda x: "".join(x[0]))

string = just('"').ignore_then(any_item[str]().repeated(just_seq('"').to("")).map(lambda x: "".join(x[0])))

object_member = (
    string.then_ignore(ws)
    .then_ignore(just(":"))
    .then(ForwardRefParser(lambda: element))
)
object_members: Parser[str, dict[str, Element]] = object_member.then(
    choose(
        just(",").then(ws).ignore_then(ForwardRefParser(lambda: object_members)),
        just("}").map(lambda _: {}),
    )
).map(lambda x: {x[0][0]: x[0][1], **x[1]})

json_object = (
    just("{")
    .then(ws)
    .ignore_then(
        choose(just("}").map(lambda _: {}), empty[str]().ignore_then(object_members))
    )
)

list_members: Parser[str, list[Element], Literal[False]] = (
    ForwardRefParser(lambda: element)
    .then(
        choose(
            just(",").then(ws).ignore_then(ForwardRefParser(lambda: list_members)),
            just("]").map(lambda _: []),
        )
    )
    .map(lambda x: [x[0], *x[1]])
)
json_list = (
    just("[")
    .then(ws)
    .ignore_then(
        choose(just("]").map(lambda _: []), empty[str]().ignore_then(list_members))
    )
)

number_rest: Parser[str, str] = choose(
    any_of("0123456789").then(ForwardRefParser(lambda: number_rest)).map("".join),
    empty[str]().to(""),
)
number = choose(just("0"), any_of("123456789").then(number_rest).map("".join)).map(int)

element: Parser[str, Element] = ws.ignore_then(
    choose(
        json_object.map(Element),
        json_list.map(Element),
        string.map(Element),
        number.map(Element),
        just_seq("true").map(lambda _: Element(True)),
        just_seq("false").map(lambda _: Element(False)),
        just_seq("null").map(lambda _: Element(None)),
    )
).then_ignore(ws)

json_parser = start_of_file[str]().ignore_then(element).then_ignore(end_of_file[str]())

# Test implementation

import unittest


class TestParser(unittest.TestCase):
    def test_basics(self):
        self.assertEqual(json_parser("{}", 0), (Element({}), 2))
        self.assertEqual(json_parser("[]", 0), (Element([]), 2))
        self.assertEqual(json_parser('""', 0), (Element(""), 2))
        self.assertEqual(json_parser("true", 0), (Element(True), 4))
        self.assertEqual(json_parser("false", 0), (Element(False), 5))
        self.assertEqual(json_parser("null", 0), (Element(None), 4))
        self.assertEqual(json_parser("1", 0), (Element(1), 1))

    def test_errors(self):
        with self.assertRaises(ValueError):
            _ = json_parser("{", 0)
        with self.assertRaises(ValueError):
            _ = json_parser("}", 0)
        with self.assertRaises(ValueError):
            _ = json_parser("[", 0)
        with self.assertRaises(ValueError):
            _ = json_parser("]", 0)
        with self.assertRaises(ValueError):
            _ = json_parser('"', 0)
        with self.assertRaises(ValueError):
            _ = json_parser("a", 0)

    def test_complex(self):
        # fmt: off
        self.assertEqual(
            json_parser('{"a": [], "b": {"c": {}, "d": "", "e": [{" ": [{"\r\n": \r\n[true, false, null, {"true": true, "false": false, "null": null}]}]}]}}', 0),
            (Element({"a": Element([]), "b": Element({"c": Element({}), "d": Element(""), "e": Element([Element({" ": Element([Element({"\r\n": Element([Element(True), Element(False), Element(None), Element({"true": Element(True), "false": Element(False), "null": Element(None)})])})])})])})}), 127)
        )
        # fmt: on


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        print(json_parser(sys.argv[1], 0))  # ruff: ignore[T201]
    else:
        _ = unittest.main()
