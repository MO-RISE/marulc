import re
import json
import operator
from pathlib import Path
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


def parse_checksum(nmea_str):
    return reduce(operator.xor, map(ord, nmea_str), 0)


def parse_value(value: str):
    try:
        value = float(value)
        value = int(value) if value.is_integer() else value
    except ValueError:
        # Keep as string
        pass
    return value


def unpack_using_definition(definition: dict, data: list):
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


def unpack_using_talker(talker: str, data: list):
    definition = TALKER_DB["Talkers"][talker]
    out = unpack_using_definition(definition, data)
    return out


def unpack_using_proprietary(manufacturer: str, data: str):
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


def unpack_nmea_message(line: str):
    """
    Parses a string representing a NMEA 0183 sentence, and returns a
    python dictionary with the unpacked sentence
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
        cs2 = parse_checksum(nmea_str)
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
