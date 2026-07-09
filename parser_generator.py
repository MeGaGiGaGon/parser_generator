from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from typing import Literal, overload, override, Any

type ParserResult[O] = tuple[O, int]
type ParserFunc[I, O] = Callable[[Sequence[I], int], ParserResult[O]]


@contextmanager
def add_note(note: str):
    try:
        yield None
    except BaseException as e:
        e.add_note(note)
        raise


class Parser[I, O, P: (Literal[True], Literal[False])](ABC):
    # `SO` instead of just `O` because python/typing#2281
    @overload
    def predicate[SO](self: Parser[I, SO, Literal[True]]) -> Sequence[Sequence[I]]: ...
    @overload
    def predicate[SO](self: Parser[I, SO, Literal[False]]) -> None: ...
    @abstractmethod
    def predicate(self) -> Sequence[Sequence[I]] | None: ...

    @abstractmethod
    def func(self) -> ParserFunc[I, O]: ...

    @abstractmethod
    def with_new_func[U](self, func: ParserFunc[I, U]) -> Parser[I, U, P]: ...

    def __call__(self, input: Sequence[I], index: int) -> ParserResult[O]:
        return self.func()(input, index)

    def then[OO, OP: (Literal[True], Literal[False])](
        self, other: Parser[I, OO, OP]
    ) -> Parser[I, tuple[O, OO], P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[tuple[O, OO]]:
            with add_note("Inside then arm one"):
                res, index = self(input, index)
            with add_note("Inside then arm two"):
                res2, index = other(input, index)
            return (res, res2), index

        return self.with_new_func(inner)

    def then_unpack[*TS, OP: (Literal[True], Literal[False])](
        self, other: Parser[I, tuple[*TS], OP]
    ) -> Parser[I, tuple[O, *TS], P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[tuple[O, *TS]]:
            with add_note("Inside then_unpack arm one"):
                res, index = self(input, index)
            with add_note("Inside then_unpack arm two"):
                res2: tuple[*TS]  # python/mypy#21693
                res2, index = other(input, index)
            return (res, *res2), index

        return self.with_new_func(inner)

    def unpack_then[*TS, OO, OP: (Literal[True], Literal[False])](
        self: Parser[I, tuple[*TS], P], other: Parser[I, OO, OP]
    ) -> Parser[I, tuple[*TS, OO], P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[tuple[*TS, OO]]:
            with add_note("Inside unpack_then arm one"):
                res: tuple[*TS]  # python/mypy#21693
                res, index = self(input, index)
            with add_note("Inside unpack_then arm two"):
                res2, index = other(input, index)
            return (*res, res2), index

        return self.with_new_func(inner)

    def ignore_then[OO, OP: (Literal[True], Literal[False])](
        self, other: Parser[I, OO, OP]
    ) -> Parser[I, OO, P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[OO]:
            with add_note("Inside ignore_then arm one"):
                _, index = self(input, index)
            with add_note("Inside ignore_then arm two"):
                return other(input, index)

        return self.with_new_func(inner)

    def then_ignore[OO, OP: (Literal[True], Literal[False])](
        self, other: Parser[I, OO, OP]
    ) -> Parser[I, O, P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[O]:
            with add_note("Inside then_ignore arm one"):
                res, index = self(input, index)
            with add_note("Inside then_ignore arm two"):
                _, index = other(input, index)
            return res, index

        return self.with_new_func(inner)

    def map[OO](self, func: Callable[[O], OO]) -> Parser[I, OO, P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[OO]:
            with add_note("Inside map"):
                res, index = self(input, index)
            return func(res), index

        return self.with_new_func(inner)

    def star_map[*TS, OO](
        self: Parser[I, tuple[*TS], P], func: Callable[[*TS], OO]
    ) -> Parser[I, OO, P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[OO]:
            with add_note("Inside star map"):
                res, index = self(input, index)
            return func(*res), index

        return self.with_new_func(inner)

    def to[OO](self, item: OO) -> Parser[I, OO, P]:
        def inner(input: Sequence[I], index: int) -> ParserResult[OO]:
            with add_note("Inside to"):
                _, index = self(input, index)
            return item, index

        return self.with_new_func(inner)


class PredicateParser[I, O](Parser[I, O, Literal[True]]):
    def __init__(
        self, func: ParserFunc[I, O], predicate: Sequence[Sequence[I]]
    ) -> None:
        self._func: ParserFunc[I, O] = func
        self._predicate: Sequence[Sequence[I]] = predicate

    @overload
    def predicate(self: Parser[I, O, Literal[True]]) -> Sequence[Sequence[I]]: ...
    @overload
    def predicate(self: Parser[I, O, Literal[False]]) -> None: ...
    @override
    def predicate(self) -> Sequence[Sequence[I]] | None:
        return self._predicate

    @override
    def func(self) -> ParserFunc[I, O]:
        return self._func

    @override
    def with_new_func[U](self, func: ParserFunc[I, U]) -> PredicateParser[I, U]:
        return PredicateParser(func, self._predicate)


class SimpleParser[I, O](Parser[I, O, Literal[False]]):
    def __init__(self, func: ParserFunc[I, O]) -> None:
        self._func: ParserFunc[I, O] = func

    @overload
    def predicate(self: Parser[I, O, Literal[True]]) -> Sequence[Sequence[I]]: ...
    @overload
    def predicate(self: Parser[I, O, Literal[False]]) -> None: ...
    @override
    def predicate(self) -> Sequence[Sequence[I]] | None:
        return None

    @override
    def func(self) -> ParserFunc[I, O]:
        return self._func

    @override
    def with_new_func[U](self, func: ParserFunc[I, U]) -> SimpleParser[I, U]:
        return SimpleParser(func)


class ForwardRefParser[I, O](Parser[I, O, Literal[False]]):
    def __init__(self, func: Callable[[], ParserFunc[I, O]]) -> None:
        self._func: Callable[[], ParserFunc[I, O]] = func

    @overload
    def predicate(self: Parser[I, O, Literal[True]]) -> Sequence[Sequence[I]]: ...
    @overload
    def predicate(self: Parser[I, O, Literal[False]]) -> None: ...
    @override
    def predicate(self) -> Sequence[Sequence[I]] | None:
        return None

    @override
    def func(self) -> ParserFunc[I, O]:
        return self._func()

    @override
    def with_new_func[U](self, func: ParserFunc[I, U]) -> SimpleParser[I, U]:
        return SimpleParser(func)


def choose[I, O](*parsers: Parser[I, O, Literal[True]]) -> Parser[I, O, Literal[True]]:
    new_predicates: list[Sequence[I]] = []
    for parser in parsers:
        for predicate in parser.predicate():
            for higher_precedence_predicate in new_predicates:
                if len(predicate) < len(higher_precedence_predicate):
                    continue
                if all(
                    predicate[index] == higher_precedence_predicate[index]
                    for index in range(len(higher_precedence_predicate))
                ):
                    msg = f"Predicate {predicate!r} is overlapped by shorter predicate {higher_precedence_predicate!r} and will never apply"
                    raise ValueError(msg)
            new_predicates.append(predicate)

    def inner(input: Sequence[I], index: int) -> ParserResult[O]:
        for parser in parsers:
            for seq in parser.predicate():
                seq_index = 0
                temp_index = index
                while temp_index < len(input) and seq_index < len(seq):
                    if input[temp_index] != seq[seq_index]:
                        break
                    seq_index += 1
                    temp_index += 1
                if seq_index < len(seq):
                    continue
                try:
                    return parser(input, index)
                except ValueError as e:
                    e.add_note(
                        f"Matched {seq=!r} out of {new_predicates=!r} at {input[index : index + 10]!r} {index=}"
                    )
                    raise
        msg = f"No parser predicates matched the input\nSample of input: {input[index : index + 10]!r}\n{new_predicates=!r}"
        raise ValueError(msg)

    return PredicateParser(inner, new_predicates)


def just[I](item: I) -> PredicateParser[I, I]:
    def inner(input: Sequence[I], index: int) -> ParserResult[I]:
        if index < len(input):
            if input[index] == item:
                return item, index + 1
            msg = f"Expected {item!r}, got {input[index : index + 10]!r} {input[index : index + 10]!r} ({index=})"
            raise ValueError(msg)
        msg = f"Expected {item!r}, but input ran out at {index=}"
        raise ValueError(msg)

    return PredicateParser(inner, [[item]])


def just_seq[I](seq: Sequence[I]) -> PredicateParser[I, Sequence[I]]:
    def inner(input: Sequence[I], index: int) -> ParserResult[Sequence[I]]:
        seq_index = 0
        while index < len(input) and seq_index < len(seq):
            if input[index] != seq[seq_index]:
                msg = f"Expected {seq[seq_index]!r} (part of {seq=!r}), got {input[index]!r} ({index=})"
                raise ValueError(msg)
            seq_index += 1
            index += 1
        if seq_index < len(seq):
            msg = f"Expected {seq[seq_index]!r} (part of {seq=!r}), but input ran out at {index=}"
            raise ValueError(msg)
        return seq, index

    return PredicateParser(inner, [seq])


def any_of[I](values: Sequence[I]) -> PredicateParser[I, I]:
    def inner(input: Sequence[I], index: int) -> ParserResult[I]:
        if not index < len(input):
            msg = f"Input ran empty inside any_of\n{values=!r} ({index=})"
            raise ValueError(msg)
        for item in values:
            if input[index] == item:
                return item, index + 1
        msg = f"Expected one of {values!r}, got {input[index]!r} ({index=})"
        raise ValueError(msg)

    return PredicateParser(inner, [[x] for x in values])


def any_item() -> PredicateParser[Any, Any]:  # pyright: ignore[reportExplicitAny]
    def inner(input: Sequence[Any], index: int) -> ParserResult[Any]:  # pyright: ignore[reportExplicitAny]
        if not index < len(input):
            msg = f"Input ran empty inside any_item ({index=})"
            raise ValueError(msg)
        return input[index], index + 1

    return PredicateParser(inner, [[]])


def empty() -> PredicateParser[Any, None]:  # pyright: ignore[reportExplicitAny]
    def inner(_: Sequence[Any], index: int) -> ParserResult[None]:  # pyright: ignore[reportExplicitAny]
        return None, index

    return PredicateParser(inner, [[]])
