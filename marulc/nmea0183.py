"""Containing functionality for unpacking textual NMEA0183 messages
"""
import re
import json
import operator
from pathlib import Path
from typing import Sequence, Union, Optional, Dict, Type, Callable
from functools import reduce

from marulc.parser_bases import (
    RawParserBase,
    NMEA0183FormatterBase,
    NMEA0183StandardFormatterBase,
    NMEA0183ProprietaryFormatterBase,
)
from marulc.exceptions import ParseError, SentenceTypeError, ChecksumError

# Read Sentence Formatter definitions from file
DB_PATH = Path(__file__).parent / "nmea0183_sentence_formatters.json"
with DB_PATH.open() as f_handle:
    db = json.load(f_handle)

STANDARD_SENTENCE_FORMATTERS = db["Standard"]
PROPRIETARY_SENTENCE_FORMATTERS = db["Proprietary"]


def get_description_for_sentence_formatter(sentence_formatter: str) -> dict:
    """Get the description and template for this sentence formatter
    Args:
        sentence_formatter (str): Sentence formatter
    Returns:
        dict: Description
    """
    descr = STANDARD_SENTENCE_FORMATTERS.get(
        sentence_formatter
    ) or PROPRIETARY_SENTENCE_FORMATTERS.get(sentence_formatter)
    if not descr:
        raise ValueError(f"No knowledge of the sentence formatter {sentence_formatter}")

    return descr


# REGEXes
SENTENCE_REGEX = re.compile(
    r"""
    # start of string, optional whitespace, optional '$'
    ^\s*\$?

    # message (from '$' or start to checksum or end, non-inclusve)
    (?P<nmea_str>
        # sentence type identifier
        (?P<sentence_type>

            # proprietary sentence
            (P\w{3})|

            # query sentence, ie: 'CCGPQ,GGA'
            # NOTE: this should have no data
            (\w{2}\w{2}Q,\w{3})|

            # talker sentence, ie: 'GPGGA'
            (\w{2}\w{3},)|
        )

        # rest of message
        (?P<data>[^*]*)

    )
    # checksum: *HH
    (?:[*](?P<checksum>[A-F0-9]{2}))?

    # optional trailing whitespace
    \s*[\r\n]*$
    """,
    re.X | re.IGNORECASE,
)
TALKER_REGEX = re.compile(r"^(?P<talker>\w{2})(?P<sentence_formatter>\w{3}),$")
QUERY_REGEX = re.compile(
    r"^(?P<talker>\w{2})(?P<listener>\w{2})Q,(?P<sentence_formatter>\w{3})$"
)
PROPRIETARY_REGEX = re.compile(r"^P(?P<manufacturer>\w{3})$")


def calculate_checksum(nmea_str: str) -> int:
    """Calculate checksum from inputted raw nmea string

    Args:
        nmea_str (str): Raw received nmea string

    Returns:
        int: Calculated checksum
    """
    return reduce(operator.xor, map(ord, nmea_str), 0)


def parse_value(value: str) -> Union[str, int, float]:
    """Parses a value to either str, int or float depending on format

    Args:
        value (str): Inputted raw string

    Returns:
        Union[str, int, float]: Parsed output
    """
    try:
        value = float(value)
        value = int(value) if value.is_integer() else value
    except ValueError:
        # Keep as string
        pass
    return value


def unpack_using_definition(definition: dict, data: list) -> dict:
    """Unpack a list of data elements using the provided definition

    Args:
        definition (dict): Definition describing how the data should be interpreted
        data (list): Raw data elements

    Returns:
        dict: Unpacked data including parsed values and descriptions
    """
    out = {"Fields": {}}

    for field, value in zip(definition["Fields"], data):
        out["Fields"][field["Id"]] = parse_value(value)

    return out


def unpack_using_proprietary(manufacturer: str, data: str) -> dict:
    """Unpack a raw, proprietary message based on knowledge about the manufacturer

    Args:
        manufacturer (str): Manufacturer acronym
        data (str): Raw data elements

    Raises:
        ParseError: If a definition could not be found for this proprietary message

    Returns:
        dict: Unpacked data including parsed values and descriptions
    """
    manufacturer_def = PROPRIETARY_SENTENCE_FORMATTERS[manufacturer]

    # Try to figure out the identifier of the message type
    first = parse_value(data[0])
    second = parse_value(data[1])
    identifier = first + (second if isinstance(second, str) else "")

    if identifier in manufacturer_def["Sentences"]:
        definition = manufacturer_def["Sentences"][identifier]
        out = unpack_using_definition(definition, data)
        out["Talker"] = manufacturer
        out["Formatter"] = identifier
        return out

    raise ParseError(
        "Could not find a definition for this proprietary sentence",
        list(manufacturer, identifier, *data),
    )


def unpack_nmea0183_message(  # pylint: disable=too-many-locals, too-many-statements
    line: str,
    standard_custom_formatters: Optional[Dict[str, Callable]] = None,
    proprietary_custom_formatters: Optional[Dict[str, Callable]] = None,
) -> dict:
    """Parses a string representing a NMEA 0183 sentence, and returns a
    python dictionary with the unpacked sentence

    Args:
        line (str): Raw NMEA0183 sentence
        standard_custom_formatters (Optional[Dict[str, Callable]]): Dict with custom sentence
            formatters. Keys are sentence formatter strings (ex. 'PGN') and values are
            callables returning a parsed message for the specific sentence formatter.
        proprietary_custom_formatters (Optional[Dict[str, Callable]]): Dict with custom sentence
            formatters. Keys are sentence formatter strings (ex. 'PGN') and values are
            callables returning a parsed message for the specific sentence formatter.

    Raises:
        ParseError:
            If parsing of message fails
        ChecksumError:
            If checksum does not match
        SentenceTypeError:
            If the inputted NMEA sentence is of a type that is not supported

    Returns:
        dict: Complete unpacked message
    """
    match = SENTENCE_REGEX.match(line)
    if not match:
        raise ParseError("could not parse data", line)

    # Unpack groups
    nmea_str = match.group("nmea_str")
    data_str = match.group("data")
    checksum = match.group("checksum")
    sentence_type = match.group("sentence_type").upper()
    data = data_str.split(",")

    if checksum:
        cs1 = int(checksum, 16)
        cs2 = calculate_checksum(nmea_str)
        if cs1 != cs2:
            raise ChecksumError(
                f"checksum does not match: {cs1:#02X} != {cs2:#02X}", data
            )

    # Is this a regular NMEA0183 sentence?
    talker_match = TALKER_REGEX.match(sentence_type)
    if talker_match:
        talker = talker_match.group("talker")
        sentence_formatter = talker_match.group("sentence_formatter")

        # Check if we have a custom formatter for this sentence
        formatters = standard_custom_formatters or {}
        if sentence_formatter in formatters:
            output = formatters[sentence_formatter](data)
            output["Talker"] = talker
            output["Formatter"] = sentence_formatter
            return output

        if sentence_formatter in STANDARD_SENTENCE_FORMATTERS:
            definition = STANDARD_SENTENCE_FORMATTERS[sentence_formatter]
            output = unpack_using_definition(definition, data)
            output["Talker"] = talker
            output["Formatter"] = sentence_formatter
            return output

        raise ParseError(
            "Could not find a definition for this NMEA sentence!", nmea_str
        )

    # Is this a query sentence?
    query_match = QUERY_REGEX.match(sentence_type)
    if query_match and not data_str:
        raise SentenceTypeError("Query sentences not supported!", nmea_str)

    # Is this a proprietary sentence?
    proprietary_match = PROPRIETARY_REGEX.match(sentence_type)
    if proprietary_match:

        manufacturer = proprietary_match.group("manufacturer")

        # Try to figure out the identifier of the message type
        first = parse_value(data[0])
        second = parse_value(data[1])
        identifier = first + (second if isinstance(second, str) else "")

        # Check if we have a custom formatter for this sentence
        formatters = proprietary_custom_formatters or {}
        if manufacturer in formatters:
            output = formatters[manufacturer](data)
            output["Talker"] = manufacturer
            output["Formatter"] = identifier
            return output

        # Otherwise, try our library of proprietary sentences
        manufacturer_def = PROPRIETARY_SENTENCE_FORMATTERS.get(manufacturer)

        if manufacturer_def and (identifier in manufacturer_def["Sentences"]):
            definition = manufacturer_def["Sentences"][identifier]
            out = unpack_using_definition(definition, data)
            out["Talker"] = manufacturer
            out["Formatter"] = identifier
            return out

        raise ParseError(
            "Could not find a definition for this proprietary sentence", nmea_str
        )

    raise ParseError("Malformed NMEA0183 sentence!", nmea_str)


class NMEA0183Parser(RawParserBase):  # pylint: disable=too-few-public-methods
    """A parser for parsing raw NMEA0183 strings"""

    def __init__(
        self,
        custom_formatters: Optional[Sequence[Type[NMEA0183FormatterBase]]] = None,
    ) -> None:
        super().__init__()
        self._standard_formatters = {}
        self._proprietary_formatters = {}
        custom_formatters = custom_formatters or []

        for fmt in custom_formatters:
            if isinstance(fmt, NMEA0183StandardFormatterBase):
                self._standard_formatters[fmt.sentence_formatter()] = fmt.unpack
            elif isinstance(fmt, NMEA0183ProprietaryFormatterBase):
                self._proprietary_formatters[fmt.manufacturer_code()] = fmt.unpack
            else:
                raise ValueError("Unknown custom parser type!", type(fmt))

    def unpack(self, msg: str) -> dict:
        return unpack_nmea0183_message(
            msg, self._standard_formatters, self._proprietary_formatters
        )
