"""Utility functions
"""
import re
from typing import Any, Callable, Iterable, Type
from functools import reduce, partial

from jasmine.parser_bases import RawParserBase
from jasmine.exceptions import MultiPacketError, ParseError

Filter = Callable[[Iterable[dict]], Iterable[dict]]


def parse_from_iterator(
    parser: Type[RawParserBase], source: Iterable[str], quiet=False
) -> Iterable[dict]:
    """Helper function for unpacking NMEA sentences from an iterable source

    Args:
        parser (Type[RawParserBase]): Parser conforming to the RawParser interface.
        source (Iterable[str]): Iterable source which yields NMEA 0183 sentences
        quiet (bool, optional): Whether exceptions encountered should be raised or
            silenced. Defaults to False.

    Yields:
        Iterator[Iterable[dict]]: The next, complete, unpacked message as a python
            dictionary.
    """

    for sentence in source:
        try:
            yield parser.unpack(sentence)
        except MultiPacketError:
            # Never do anything about MultiPacketErrors
            pass
        except ParseError:
            if not quiet:
                raise


def deep_get(dikt: dict, *keys: str, default: Any = None) -> Any:
    """A "deep getter" for nested dictionaries

    .. highlight:: python
    .. code-block:: python

        from jasmine.utils import deep_get

        d = {"A": {"B":{"C":"3}}}
        deep_get(d, "A", "B", "C") # Returns 3
        deep_get(d, "A", "B", "C", "D") # Returns None
        deep_get(d, "A", "B", "C", "D", default=89) # Returns 89

    Args:
        dikt (dict): Nested dictionary to operate on
        *keys (str): Any number of keys in descending level in hte nested dictionary.
        default (Any, optional): Default value to return if chain of keys cant be
            followed. Defaults to None.

    Returns:
        Any: The value found at the bottom of the keys or the default value.
    """

    return (
        reduce(
            lambda d, k: d.get(k) if (d and isinstance(d, dict)) else None, keys, dikt
        )
        or default
    )


def filter_on_talker_formatter(
    *regexes: str,
) -> Filter:
    """Create filter that filters on specific talkers and/or sentence formatters

    .. highlight:: python
    .. code-block:: python

        from jasmine import parse_from_iterator
        from jasmine.utils import filter_on_talker_formatter

        source = open("nmea_log.txt")
        filtered = filter_on_talker_formatter("..GGA", "PASHR")(parse_from_iterator(source))

    Args:
        *regexes (str): Any number of strings or regex expressions that
            will be matched against a "Talker" and "Formatter" key combination.

    Returns:
        Callable[[Iterable[dict]], Iterable[dict]]: A pre-loaded filter callable
    """
    patterns = [re.compile(r) for r in regexes]
    return partial(
        filter,
        lambda item: any(
            pattern.match(item.get("Talker", "") + item.get("Formatter", ""))
            for pattern in patterns
        ),
    )


def filter_on_pgn(*PGNs: int) -> Filter:
    """Create filter that filters on specific PGN numbers

    .. highlight:: python
    .. code-block:: python

        from jasmine import parse_from_iterator
        from jasmine.utils import filter_on_pgn

        source = open("nmea_log.txt")
        filtered = filter_on_pgn(127488)(parse_from_iterator(source))

    Args:
        *PGNs (str): Any number of PGN numbers that will be matched against a
            "PGN" key.

    Returns:
        Callable[[Iterable[dict]], Iterable[dict]]: A pre-loaded filter callable
    """
    return partial(filter, lambda item: item.get("PGN") in PGNs)
