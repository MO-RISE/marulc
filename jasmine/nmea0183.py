"""Containing functionality for unpacking textual NMEA0183 messages

Code is heavily inspired by pynmea2
"""
import re
import json
import operator
from pathlib import Path
from typing import Union
from functools import reduce

from jasmine.nmea2000 import unpack_PGN_message
from jasmine.exceptions import ParseError, SentenceTypeError, ChecksumError

# Read Talker definitions from file
DB_PATH = Path(__file__).parent / "talkers.json"
with DB_PATH.open() as f_handle:
    TALKER_DB = json.load(f_handle)

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

            # taker sentence, ie: 'GPGGA'
            (\w{2}\w{3},)
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
TALKER_REGEX = re.compile(r"^(?P<talker>\w{2})(?P<sentence>\w{3}),$")
QUERY_REGEX = re.compile(r"^(?P<talker>\w{2})(?P<listener>\w{2})Q,(?P<sentence>\w{3})$")
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
    out = {
        "Description": definition["Description"],
        "Fields": dict(),
    }

    for field, value in zip(definition["Fields"], data):
        out["Fields"][field["Id"]] = {
            "Description": field["Description"],
            "Value": parse_value(value),
        }

    return out


def unpack_using_talker(talker: str, data: list) -> dict:
    """Unpack a raw message based on knowledge about which talker sent it

    Args:
        talker (str): A talker acronym
        data (list): Raw data elements

    Raises:
        ParseError: If a matching talker could not be found

    Returns:
        dict: Unpacked data including parsed values and descriptions
    """
    definition = TALKER_DB["Talkers"].get(talker)
    if not definition:
        raise ParseError("No matching talker!", list(talker, data))
    out = unpack_using_definition(definition, data)
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
    manufacturer_def = TALKER_DB["Proprietary"][manufacturer]

    # Try to figure out the identifier of the message type
    first = parse_value(data[0])
    second = parse_value(data[1])
    identifier = first + (second if isinstance(second, str) else "")

    if identifier in manufacturer_def["Sentences"]:
        definition = manufacturer_def["Sentences"][identifier]
        out = unpack_using_definition(definition, data)
        out["Talker"] = f"{manufacturer}{identifier}"
        return out

    raise ParseError(
        "Could not find a definition for this proprietary string",
        list(manufacturer, identifier, *data),
    )


def unpack_nmea_message(  # pylint: disable=too-many-locals,inconsistent-return-statements
    line: str,
) -> dict:
    """Parses a string representing a NMEA 0183 sentence, and returns a
    python dictionary with the unpacked sentence

    Args:
        line (str): Raw NMEA0183 sentence

    Raises:
        ParseError: If parsing of message fails
        ChecksumError: If checksum does not match
        SentenceTypeError: If the inputted NMEA sentence is of a type that is not
            supported
        MultiPacketDiscardedError: If this subpacket is discarded due to missing
            messages
        MultiPacketInProcessError: If this subpacket has been processed successfully
            but we require more subpackets to be able to decode the full message

    Returns:
        dict: [description]
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
                "checksum does not match: %02X != %02X" % (cs1, cs2), data
            )

    # Is this a regular NMEA0183 sentence?
    talker_match = TALKER_REGEX.match(sentence_type)
    if talker_match:
        talker = talker_match.group("talker")
        sentence = talker_match.group("sentence")

        if sentence == "PGN":
            # This is a wrapped NMEA2000 message!
            output = unpack_PGN_message(data)
            output["Talker"] = f"{talker}{sentence}"
            return output

        if sentence in TALKER_DB["Talkers"]:
            output = unpack_using_talker(sentence, data)
            output["Talker"] = f"{talker}{sentence}"
            return output

        raise ParseError("Could not find a definition for this NMEA string!", nmea_str)

    # Is this a query sentence?
    query_match = QUERY_REGEX.match(sentence_type)
    if query_match and not data_str:
        raise SentenceTypeError("Query sentences not supported!", nmea_str)

    # Is this a proprietary sentence?
    proprietary_match = PROPRIETARY_REGEX.match(sentence_type)
    if proprietary_match:
        manufacturer = proprietary_match.group("manufacturer")

        if manufacturer in TALKER_DB["Proprietary"]:
            return unpack_using_proprietary(manufacturer, data)

        raise ParseError("Could not find a definition for this NMEA string!", nmea_str)
