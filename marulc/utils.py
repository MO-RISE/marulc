"""Utility functions
"""
import re
from typing import Any, Callable, Iterable, Type
from functools import reduce

from marulc.parser_bases import RawParserBase
from marulc.exceptions import MultiPacketError, ParseError

Filter = Callable[[dict], bool]


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

        from marulc.utils import deep_get

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
    value = reduce(
        lambda d, k: d.get(k) if (d and isinstance(d, dict)) else None, keys, dikt
    )
    return default if value is None else value


def filter_on_talker_formatter(
    *regexes: str,
) -> Filter:
    """Create filter that filters on specific talkers and/or sentence formatters

    .. highlight:: python
    .. code-block:: python

        from marulc import parse_from_iterator
        from marulc.utils import filter_on_talker_formatter

        source = open("nmea_log.txt")
        filtered = filter_on_talker_formatter("..GGA", "PASHR")(parse_from_iterator(source))

    Args:
        *regexes (str): Any number of strings or regex expressions that
            will be matched against a "Talker" and "Formatter" key combination.

    Returns:
        Callable[[dict], bool]: A pre-loaded filter callable
    """
    patterns = [re.compile(r) for r in regexes]
    return lambda item: any(
        pattern.match(item.get("Talker", "") + item.get("Formatter", ""))
        for pattern in patterns
    )


def filter_on_pgn(*PGNs: int) -> Filter:
    """Create filter that filters on specific PGN numbers

    .. highlight:: python
    .. code-block:: python

        from marulc import parse_from_iterator
        from marulc.utils import filter_on_pgn

        source = open("nmea_log.txt")
        filtered = filter_on_pgn(127488)(parse_from_iterator(source))

    Args:
        *PGNs (str): Any number of PGN numbers that will be matched against a
            "PGN" key.

    Returns:
        Callable[[dict], bool]: A pre-loaded filter callable
    """
    return lambda item: item.get("PGN") in PGNs
