"""Module containg abstract base class for different kind of parsers
"""
from typing import Any, List
from abc import ABC, abstractmethod

# pylint: disable=too-few-public-methods


class ParserBase(ABC):
    """An abstract base class for all parsers"""

    @abstractmethod
    def unpack(self, msg: Any) -> dict:
        """Unpack a message using this parser

        Args:
            msg (Any): Message to be unpacked
        """


class RawParserBase(ParserBase):
    """An abstract base class for parsers that parse raw data"""


class NMEA0183FormatterBase(ParserBase):
    """An abstract base class for parsers that takes a valid NMEA0183 message
    as a list of strings and unpacks it"""

    @abstractmethod
    def unpack(self, msg: List[str]) -> dict:
        """Unpack a NMEA0183 sentence using this sentence formatter

        Args:
            msg (List[str]): Message to be unpacked
        """


class NMEA0183StandardFormatterBase(NMEA0183FormatterBase):
    """An abstract base class for parsers that takes a valid NMEA0183 message
    of standard format and unpacks it"""

    @abstractmethod
    def sentence_formatter(self) -> str:
        """Which sentence formatter this parser is valid for

        Returns:
            str: Sentence formatter
        """


class NMEA0183ProprietaryFormatterBase(NMEA0183FormatterBase):
    """An abstract base class for parsers that takes a valid NMEA0183 message
    of proprietary format and unpacks it"""

    @abstractmethod
    def manufacturer_code(self) -> str:
        """Which manufacturer code this parser is valid for

        Returns:
            str: 3-digit manufacturer code
        """
