"""Package for parsing/decoding NMEA0183 and NMEA2000 messages
"""
from typing import Iterable

from jasmine.nmea0183 import unpack_nmea_message
from jasmine.exceptions import MultiPacketError, ParseError


def parse_from_iterator(source: Iterable[str], quiet=False) -> Iterable[dict]:
    """Helper function for unpacking NMEA sentences from an iterable source

    Args:
        source (Iterable[str]): Iterable source which yields NMEA 0183 sentences
        quiet (bool, optional): Whether exceptions encountered should be raised or
            silenced. Defaults to False.

    Yields:
        Iterator[Iterable[dict]]: The next, complete, unpacked message as a python
            dictionary.
    """

    for sentence in source:
        try:
            yield unpack_nmea_message(sentence)
        except MultiPacketError:
            # Never do anything about MultiPacketErrors
            pass
        except ParseError:
            if not quiet:
                raise
