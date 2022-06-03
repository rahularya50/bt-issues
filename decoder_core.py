from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, Optional, Type, TypeVar, Union


class DType(Enum):
    str = 0
    int = 1
    none = 2


STR = DType.str
INT = DType.int
NONE = DType.none


class Rest(Enum):
    rest = 0


REST = Rest.rest


class Skip:
    n: int

    def __init__(self) -> None:
        self.n = 1

    def __mul__(self, other: int) -> "Skip":
        out = Skip()
        out.n = self.n * other
        return out


SKIP = Skip()
T = TypeVar("T", bound="Decodable")
Pattern = Union[Type["Decodable"], "Shape", "OneOf", DType, str, "ListOf", Skip]
ShapeField = Union[Pattern, Rest]


class MatchFailure(ValueError):
    pass


U = TypeVar("U")


def match_instance(x: object, t: Type[U], msg: Optional[str] = None) -> U:
    if not isinstance(x, t):
        if msg is None:
            raise MatchFailure(f"Expected {x} to be a {t}")
        raise MatchFailure(msg)
    return x


def match_check(cond: bool, msg: str) -> None:
    if not cond:
        raise MatchFailure(msg)


@dataclass
class Shape:
    children: List[ShapeField]

    def __init__(self, *args: ShapeField):
        self.children = list(args)

    def __iter__(self) -> Iterator[ShapeField]:
        return iter(self.children)

    def __len__(self) -> int:
        return len(self.children)

    def __getitem__(self, item: int) -> ShapeField:
        return self.children[item]


@dataclass
class OneOf:
    candidates: List[Pattern]

    def __init__(self, *args: Pattern):
        self.candidates = list(args)

    def __iter__(self) -> Iterator[ShapeField]:
        return iter(self.candidates)

    def __len__(self) -> int:
        return len(self.candidates)


@dataclass
class ListOf:
    type: Pattern


class Decodable:
    PATTERN: Pattern

    @classmethod
    def decode(cls: Type[T], fields: object) -> T:
        contents: List[Union[str, int, Decodable]] = []

        def consume_pattern(
            curr: object,
            pattern: Pattern,
            out: List[Union[str, int, Decodable]],
        ) -> None:
            if isinstance(pattern, type) and issubclass(pattern, Decodable):
                match_instance(curr, list)
                out.append(pattern.decode(curr))
            elif isinstance(pattern, DType):
                if pattern is DType.str:
                    curr = match_instance(curr, str)
                    out.append(curr)
                elif pattern is DType.int:
                    # TODO: allow int literals as well
                    curr = match_instance(curr, str)
                    out.append(int(curr))
                elif pattern is DType.none:
                    match_check(curr is None, f"Expected None, got {curr}")
                else:
                    assert_never(pattern)
            elif isinstance(pattern, Shape):
                curr = match_instance(curr, list)
                match_i = 0
                for field_type in pattern:
                    if field_type is REST:
                        break
                    elif isinstance(field_type, Skip):
                        match_i += field_type.n
                        continue

                    match_check(
                        match_i < len(curr),
                        f"Too few fields (expected at least {match_i}, got {len(curr)})",
                    )
                    consume_pattern(curr[match_i], field_type, out)
                    match_i += 1
                else:
                    match_check(
                        match_i == len(curr),
                        f"Too many fields (expected {match_i}, got {len(curr)}). Use REST if this is allowed.",
                    )
                match_check(
                    match_i <= len(curr),
                    f"Skipped too many fields (expected total of {match_i}, got {len(curr)}).",
                )

            elif isinstance(pattern, str):
                match_check(curr == pattern, f"Expected {pattern}, got {curr}")
            elif isinstance(pattern, Skip):
                assert pattern.n == 1, "Skips outside of Shapes cannot be repeated"
            elif isinstance(pattern, ListOf):
                curr = match_instance(curr, list)
                for x in curr:
                    consume_pattern(x, pattern.type, contents)
            elif isinstance(pattern, OneOf):
                for candidate in pattern.candidates:
                    candidate_out: List[Union[str, int, Decodable]] = []
                    try:
                        consume_pattern(curr, candidate, candidate_out)
                        out.extend(candidate_out)
                        return
                    except MatchFailure:
                        continue
                raise MatchFailure("No OneOf branches succeeded")
            else:
                assert_never(pattern)

        consume_pattern(fields, cls.PATTERN, contents)
        return cls(*contents)
