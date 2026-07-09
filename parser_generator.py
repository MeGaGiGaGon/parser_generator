import abc
from types import EllipsisType
from typing import Literal, final, overload, override
from collections.abc import Callable, Sequence

debug = True
debug_depth = 0

def debug_print[I](input: Sequence[I], index: int, s: str):
    print(f"{"  " * debug_depth}{input[index:index+5]!r} {s}")

# Cannot use dataclasses for these because in
# 3.13+ all dataclass generics are invariant
# and these should be covariant
@final
class Ok[T]:
    __match_args__ = ("_value",)
    def __init__(self, value: T):
        self._value: T = value
    
    @override
    def __repr__(self) -> str:
        return f"Ok({self._value!r})"
    
    def to_value(self) -> T:
        return self._value

# Err is not generic because we don't want to carry any data through it
@final
class Err: ...

type Result[T] = Ok[T] | Err

type ParserResult[O] = Result[tuple[int, O]]
type ParserFunc[I, O] = Callable[[Sequence[I], int], ParserResult[O]]

def simple_parser[I, O](parser: ParserFunc[I, O]) -> Parser[I, O]:
    return SimpleParser(parser)

class Parser[I, O](abc.ABC):
    @property
    @abc.abstractmethod
    def func(self) -> ParserFunc[I, O]:
        ...

    def __call__(self, input: Sequence[I], index: int) -> ParserResult[O]:
        return self.func(input, index)

    def ok_to[NEW_O](self, to: NEW_O) -> Parser[I, NEW_O]:
        def inner(input: Sequence[I], index: int) -> ParserResult[NEW_O]:
            match self.func(input, index):
                case Ok((index, _)):
                    return Ok((index, to))
                case Err() as e:
                    return e
        return SimpleParser(inner)
    
    def err_to_ok[NEW_O](self, to: NEW_O) -> Parser[I, O | NEW_O]:
        def inner(input: Sequence[I], index: int) -> ParserResult[O | NEW_O]:
            match self.func(input, index):
                case Ok() as ok:
                    return ok
                case Err():
                    return Ok((index, to))
        return SimpleParser(inner)

    def map_ok[NEW_O](self, func: Callable[[O], NEW_O]) -> Parser[I, NEW_O]:
        def inner(input: Sequence[I], index: int) -> ParserResult[NEW_O]:
            match self.func(input, index):
                case Ok((index, output)):
                    return Ok((index, func(output)))
                case Err() as e:
                    return e
        return SimpleParser(inner)

    def star_map_ok[*TS, NEW_O](self: Parser[I, tuple[*TS]], func: Callable[[*TS], NEW_O]) -> Parser[I, NEW_O]:
        def inner(input: Sequence[I], index: int) -> ParserResult[NEW_O]:
            match self.func(input, index):
                case Ok((index, output)):
                    return Ok((index, func(*output)))
                case Err() as e:
                    return e
        return SimpleParser(inner)

    def then[OO](self, other: Parser[I, OO]) -> Parser[I, tuple[O, OO]]:
        def inner(input: Sequence[I], index: int) -> ParserResult[tuple[O, OO]]:
            match self.func(input, index):
                case Ok((index, self_output)):
                    if debug:
                        debug_print(input, index, "then")
                        global debug_depth
                        debug_depth += 1
                    match other.func(input, index):
                        case Ok((index, other_output)):
                            if debug:
                                debug_depth -= 1
                            return Ok((index, (self_output, other_output)))
                        case Err() as e:
                            if debug:
                                debug_depth -= 1
                            return e
                case Err() as e:
                    return e
        return SimpleParser(inner)

    @overload
    def flatten[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12](self: Parser[I, tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[T1, T2], T3], T4], T5], T6], T7], T8], T9], T10], T11], T12]]) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12]]: ...  # pyright: ignore[reportOverlappingOverload]
    @overload
    def flatten[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11](self: Parser[I, tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[T1, T2], T3], T4], T5], T6], T7], T8], T9], T10], T11]]) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11]]: ...
    @overload
    def flatten[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10](self: Parser[I, tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[T1, T2], T3], T4], T5], T6], T7], T8], T9], T10]]) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10]]: ...
    @overload
    def flatten[T1, T2, T3, T4, T5, T6, T7, T8, T9](self: Parser[I, tuple[tuple[tuple[tuple[tuple[tuple[tuple[tuple[T1, T2], T3], T4], T5], T6], T7], T8], T9]]) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8, T9]]: ...
    @overload
    def flatten[T1, T2, T3, T4, T5, T6, T7, T8](self: Parser[I, tuple[tuple[tuple[tuple[tuple[tuple[tuple[T1, T2], T3], T4], T5], T6], T7], T8]]) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8]]: ...
    @overload
    def flatten[T1, T2, T3, T4, T5, T6, T7](self: Parser[I, tuple[tuple[tuple[tuple[tuple[tuple[T1, T2], T3], T4], T5], T6], T7]]) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7]]: ...
    @overload
    def flatten[T1, T2, T3, T4, T5, T6](self: Parser[I, tuple[tuple[tuple[tuple[tuple[T1, T2], T3], T4], T5], T6]]) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6]]: ...
    @overload
    def flatten[T1, T2, T3, T4, T5](self: Parser[I, tuple[tuple[tuple[tuple[T1, T2], T3], T4], T5]]) -> Parser[I, tuple[T1, T2, T3, T4, T5]]: ...
    @overload
    def flatten[T1, T2, T3, T4](self: Parser[I, tuple[tuple[tuple[T1, T2], T3], T4]]) -> Parser[I, tuple[T1, T2, T3, T4]]: ...
    @overload
    def flatten[T1, T2, T3](self: Parser[I, tuple[tuple[T1, T2], T3]]) -> Parser[I, tuple[T1, T2, T3]]: ...
    def flatten(self: Parser[I, tuple[object, ...]]) -> Parser[I, tuple[object, ...]]:  # pyright: ignore[reportInconsistentOverload]
        def inner(input: Sequence[I], index: int) -> ParserResult[tuple[object, ...]]:
            match self.func(input, index):
                case Ok((index, value)):
                    match value:
                        case (((((((((((a, b), c), d), e), f), g), h), i), j), k), l):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d, e, f, g, h, i, j, k, l)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case ((((((((((a, b), c), d), e), f), g), h), i), j), k):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d, e, f, g, h, i, j, k)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case (((((((((a, b), c), d), e), f), g), h), i), j):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d, e, f, g, h, i, j)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case ((((((((a, b), c), d), e), f), g), h), i):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d, e, f, g, h, i)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case (((((((a, b), c), d), e), f), g), h):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d, e, f, g, h)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case ((((((a, b), c), d), e), f), g):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d, e, f, g)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case (((((a, b), c), d), e), f):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d, e, f)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case ((((a, b), c), d), e):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d, e)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case (((a, b), c), d):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c, d)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case ((a, b), c):  # pyright: ignore[reportUnknownVariableType]
                            return Ok((index, (a, b, c)))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                        case x:
                            return Ok((index, x))
                case Err() as e:
                    return e
        return SimpleParser(inner)
    
    def then_ignore[OO](self, other: Parser[I, OO]) -> Parser[I, O]:
        def inner(input: Sequence[I], index: int) -> ParserResult[O]:
            match self.func(input, index):
                case Ok((index, self_output)):
                    if debug:
                        debug_print(input, index, "then_ignore")
                        global debug_depth
                        debug_depth += 1
                    match other.func(input, index):
                        case Ok((index, _)):
                            if debug:
                                debug_depth -= 1
                            return Ok((index, self_output))
                        case Err() as e:
                            if debug:
                                debug_depth -= 1
                            return e
                case Err() as e:
                    return e
        return SimpleParser(inner)
    
    def ignore_then[OO](self, other: Parser[I, OO]) -> Parser[I, OO]:
        def inner(input: Sequence[I], index: int) -> ParserResult[OO]:
            match self.func(input, index):
                case Ok((index, _)):
                    if debug:
                        debug_print(input, index, "ignore_then")
                        global debug_depth
                        debug_depth += 1
                    match other.func(input, index):
                        case Ok((index, other_output)):
                            if debug:
                                debug_depth -= 1
                            return Ok((index, other_output))
                        case Err() as e:
                            if debug:
                                debug_depth -= 1
                            return e
                case Err() as e:
                    return e
        return SimpleParser(inner)

    @overload
    def repeated(self, min: Literal[0], max: Literal[0] | EllipsisType = ...) -> Parser[I, tuple[()]]: ...
    @overload
    def repeated(self, min: Literal[1], max: Literal[1] | EllipsisType = ...) -> Parser[I, tuple[O]]: ...
    @overload
    def repeated(self, min: Literal[2], max: Literal[2] | EllipsisType = ...) -> Parser[I, tuple[O, O]]: ...
    @overload
    def repeated(self, min: Literal[3], max: Literal[3] | EllipsisType = ...) -> Parser[I, tuple[O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[4], max: Literal[4] | EllipsisType = ...) -> Parser[I, tuple[O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[5], max: Literal[5] | EllipsisType = ...) -> Parser[I, tuple[O, O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[0], max: Literal[1]) -> Parser[I, tuple[()] | tuple[O]]: ...
    @overload
    def repeated(self, min: Literal[0], max: Literal[2]) -> Parser[I, tuple[()] | tuple[O] | tuple[O, O]]: ...
    @overload
    def repeated(self, min: Literal[0], max: Literal[3]) -> Parser[I, tuple[()] | tuple[O] | tuple[O, O] | tuple[O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[0], max: Literal[4]) -> Parser[I, tuple[()] | tuple[O] | tuple[O, O] | tuple[O, O, O] | tuple[O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[0], max: Literal[5]) -> Parser[I, tuple[()] | tuple[O] | tuple[O, O] | tuple[O, O, O] | tuple[O, O, O, O] | tuple[O, O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[1], max: Literal[2]) -> Parser[I, tuple[O] | tuple[O, O]]: ...
    @overload
    def repeated(self, min: Literal[1], max: Literal[3]) -> Parser[I, tuple[O] | tuple[O, O] | tuple[O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[1], max: Literal[4]) -> Parser[I, tuple[O] | tuple[O, O] | tuple[O, O, O] | tuple[O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[1], max: Literal[5]) -> Parser[I, tuple[O] | tuple[O, O] | tuple[O, O, O] | tuple[O, O, O, O] | tuple[O, O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[2], max: Literal[3]) -> Parser[I, tuple[O, O] | tuple[O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[2], max: Literal[4]) -> Parser[I, tuple[O, O] | tuple[O, O, O] | tuple[O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[2], max: Literal[5]) -> Parser[I, tuple[O, O] | tuple[O, O, O] | tuple[O, O, O, O] | tuple[O, O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[3], max: Literal[4]) -> Parser[I, tuple[O, O, O] | tuple[O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[3], max: Literal[5]) -> Parser[I, tuple[O, O, O] | tuple[O, O, O, O] | tuple[O, O, O, O, O]]: ...
    @overload
    def repeated(self, min: Literal[4], max: Literal[5]) -> Parser[I, tuple[O, O, O, O] | tuple[O, O, O, O, O]]: ...
    @overload
    def repeated(self, min: int, max: int | None | EllipsisType = ...) -> Parser[I, tuple[O, ...]]: ...
    def repeated(self, min: int, max: int | None | EllipsisType = ...) -> Parser[I, tuple[O, ...]]:
        if isinstance(max, EllipsisType):
            max = min
        def inner(input: Sequence[I], index: int) -> ParserResult[tuple[O, ...]]:
            result: list[O] = []
            count = 0
            while True:
                if max is not None and count == max:
                    break
                match self.func(input, index):
                    case Ok((index, output)):
                        result.append(output)
                        count += 1
                    case Err():
                        break
            if count >= min:
                return Ok((index, tuple(result)))
            else:
                return Err()
        return SimpleParser(inner).debug("repeated")

    def separated_repeated[OO](self, separater: Parser[I, OO], min: int, max: int | None, trailing_ok: bool) -> Parser[I, Sequence[O]]:
        def inner(input: Sequence[I], index: int) -> ParserResult[Sequence[O]]:
            result: list[O] = []
            count = 0
            while True:
                if max is not None and count == max:
                    break
                if count > 0 and not trailing_ok:
                    match separater(input, index):
                        case Ok((index, _)):
                            ...
                        case Err():
                            break
                match self.func(input, index):
                    case Ok((index, output)):
                        result.append(output)
                        count += 1
                    case Err():
                        break
                if trailing_ok:
                    match separater(input, index):
                        case Ok((index, _)):
                            ...
                        case Err():
                            break
            if count >= min:
                return Ok((index, result))
            else:
                return Err()
        return SimpleParser(inner).debug("separated_repeated")

    def debug(self, message: str) -> Parser[I, O]:
        def inner(input: Sequence[I], index: int) -> ParserResult[O]:
            debug_print(input, index, message)
            global debug_depth
            debug_depth += 1
            res = self.func(input, index)
            debug_depth -= 1
            return res
        return SimpleParser(inner)
    
    def lamdebug(self, message: Callable[[], str]) -> Parser[I, O]:
        def inner(input: Sequence[I], index: int) -> ParserResult[O]:
            debug_print(input, index, message())
            global debug_depth
            debug_depth += 1
            res = self.func(input, index)
            debug_depth -= 1
            return res
        return SimpleParser(inner)


class SimpleParser[I, O](Parser[I, O]):
    def __init__(self, func: ParserFunc[I, O]):
        self._func: ParserFunc[I, O] = func
    
    @property
    @override
    def func(self) -> ParserFunc[I, O]:
        return self._func

class ForwardRefParser[I, O](Parser[I, O]):
    def __init__(self, func: Callable[[], Parser[I, O]]):
        self._metafunc: Callable[[], Parser[I, O]] = func

    @property
    @override
    def func(self) -> ParserFunc[I, O]:
        return self._metafunc()

@simple_parser
def accept[I](_: Sequence[I], index: int) -> ParserResult[None]:
    return Ok((index, None))

def just[I](item: I) -> Parser[I, I]:
    def inner(input: Sequence[I], index: int) -> ParserResult[I]:
        if index < len(input) and input[index] == item:
            return Ok((index + 1, item))
        else:
            return Err()
    return SimpleParser(inner).lamdebug(lambda: f"just {item!r}")

def just_seq[I](seq: Sequence[I]) -> Parser[I, Sequence[I]]:
    def inner(input: Sequence[I], index: int) -> ParserResult[Sequence[I]]:
        seq_index = 0
        while seq_index < len(seq):
            if index < len(input) and input[index] == seq[seq_index]:
                index += 1
                seq_index += 1
            else:
                return Err()
        return Ok((index, seq))
    return SimpleParser(inner).lamdebug(lambda: f"just_seq {seq!r}")

def any_of[I](seq: Sequence[I]) -> Parser[I, I]:
    def inner(input: Sequence[I], index: int) -> ParserResult[I]:
        if index >= len(input):
            return Err()
        for item in seq:
            if input[index] == item:
                return Ok((index + 1, item))
        return Err()
    return SimpleParser(inner).lamdebug(lambda: f"any_of {seq!r}")

class Spanned[T]:
    def __init__(self, inner: T, start: int, end: int):
        self._inner: T = inner
        self.start: int = start
        self.end: int = end
    
    def to_inner(self) -> T:
        return self._inner
    
    @override
    def __repr__(self) -> str:
        return f"Spanned(_inner={self._inner!r}, start={self.start!r}, end={self.end!r})"

def make_spanned[I, O](parser: Parser[I, O]) -> Parser[I, Spanned[O]]:
    def new_parser(input: Sequence[I], index: int) -> ParserResult[Spanned[O]]:
        result = parser(input, index)
        match result:
            case Ok():
                new_index, to_span = result.to_value()
                return Ok((new_index, Spanned(to_span, index, new_index)))
            case Err():
                return result
    return SimpleParser(new_parser)

def spanned_simple_parser[I, O](parser: ParserFunc[I, O]) -> Parser[I, Spanned[O]]:
    return make_spanned(SimpleParser(parser))

def make_meta_spanned[**P, I, O](parser_maker: Callable[P, Parser[I, O]]) -> Callable[P, Parser[I, Spanned[O]]]:
    def new_parser_maker(*args: P.args, **kwargs: P.kwargs) -> Parser[I, Spanned[O]]:
        parser = parser_maker(*args, **kwargs)
        def new_parser(input: Sequence[I], index: int) -> ParserResult[Spanned[O]]:
            result = parser(input, index)
            match result:
                case Ok():
                    new_index, to_span = result.to_value()
                    return Ok((new_index, Spanned(to_span, index, new_index)))
                case Err():
                    return result
        return SimpleParser(new_parser)
    return new_parser_maker

def choice[I, O](*parsers: tuple[Parser[I, object], Parser[I, O]]):
    def inner(input: Sequence[I], index: int) -> ParserResult[O]:
        for (predicate, parser) in parsers:
            if isinstance(predicate(input, index), Ok):
                return parser(input, index)
        raise ValueError("parser choice had no alternative selected")
    return SimpleParser(inner)
            