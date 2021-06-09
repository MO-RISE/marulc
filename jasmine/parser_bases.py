from typing import Any, List
from abc import ABC, abstractmethod


class ParserBase:
    @abstractmethod
    def unpack(self, msg: Any) -> dict:
        """Unpack a message using this parser

        Args:
            msg (Any): Message to be unpacked
        """


class RawParserBase(ParserBase):
    pass


class NMEA0183FormatterBase(ParserBase):
    @abstractmethod
    def unpack(self, msg: List[str]) -> dict:
        """Unpack a NMEA0183 sentence using this sentence formatter

        Args:
            msg (List[str]): Message to be unpacked
        """


class NMEA0183StandardFormatterBase(NMEA0183FormatterBase):
    @abstractmethod
    def sentence_formatter(self) -> str:
        """Which sentence formatter this parser is valid for

        Returns:
            str: Sentence formatter
        """


class NMEA0183ProprietaryFormatterBase(NMEA0183FormatterBase):
    @abstractmethod
    def manufacturer_code(self) -> str:
        """Which manufacturer code this parser is valid for

        Returns:
            str: 3-digit manufacturer code
        """
