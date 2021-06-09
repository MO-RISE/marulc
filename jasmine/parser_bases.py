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
    def sentence_formatter(self) -> str:
        """Which sentence formatter this parser is valid for

        Returns:
            str: Sentence formatter
        """

    @abstractmethod
    def unpack(self, msg: List[str]) -> dict:
        """Unpack a NMEA0183 sentence using this sentence formatter

        Args:
            msg (List[str]): Message to be unpacked
        """