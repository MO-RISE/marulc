"""Containing functionality for unpacking binary n2k messages according to PGN-specific definitions
"""
import json
from pathlib import Path
from copy import deepcopy

import bitstruct

from jasmine.exceptions import (
    MultiPacketDiscardedError,
    MultiPacketInProcessError,
)

# Read PGNs metadata from CANBOAT database
DB_PATH = Path(__file__).parent / "nmea2000_pgn_specifications.json"
with DB_PATH.open() as f_handle:
    PGN_DB = {item["PGN"]: item for item in json.load(f_handle)["PGNs"]}


def get_description_for_pgn(pgn: int) -> dict:
    """Get the description and template for this pgn in the format of a python
    dictionary

    Args:
        pgn (int): PGN number

    Returns:
        dict: Description
    """
    descr = PGN_DB.get(pgn)
    if not descr:
        raise ValueError(f"No knowledge of PGN {pgn}")

    return descr


def process_sub_packet(pgn: int, address: int, data: bytearray, bucket: dict):
    """Process a single subpacket part of a multi-packet n2k message. The following
    description of the protocol is taken from CANBOAT:

    NMEA 2000 uses the 8 'data' bytes as follows for fast packet type:
    data[0] is an 'order' that increments, or not (depending a bit on implementation).
    If the size of the packet <= 7 then the data follows in data[1..7]
    If the size of the packet > 7 then the next byte data[1] is the size of the payload
    and data[0] is divided into 5 bits index into the fast packet, and 3 bits 'order
    that increases.
    This means that for 'fast packets' the first bucket (sub-packet) contains 6 payload
    bytes and 7 for remaining. Since the max index is 31, the maximal payload is
    6 + 31 * 7 = 223 bytes

    Args:
        pgn (int): PGN number
        address (int): Source address of message
        data (bytearray): Raw binary packet data
        bucket (dict): Reference to temporary storage for partly parsed messages

    Raises:
        MultiPacketDiscardedError: If this subpacket is discarded due to missing
            messages
        MultiPacketInProcessError: If this subpacket has been processed successfully
            but we require more subpackets to be able to decode the full message

    Returns:
        bytearray: Complete, raw binary message stitched together from multiple subpackets
    """
    data = data[::-1]
    length = len(data) * 8  # bits
    order, idx = bitstruct.unpack(f">P{length - 8}u3u5", data)
    hashed_id = hash((pgn, address, order))

    # Too late to the party
    if idx > 0 and hashed_id not in bucket:
        raise MultiPacketDiscardedError

    # First message in a new sequence
    if idx == 0:
        (payload,) = bitstruct.unpack(">r48P16", data)
        bucket[hashed_id] = {"payload": payload, "counter": 1}
        raise MultiPacketInProcessError

    # Fetch existing bucket
    buffer = bucket[hashed_id]

    # Check for fck-up
    if buffer["counter"] != idx:
        # Dropped sub-package
        del bucket[hashed_id]
        raise MultiPacketDiscardedError

    # Still on track, append this payload to existing one!
    (payload,) = bitstruct.unpack(f">r{length - 8}P8", data)
    buffer["payload"] = payload + buffer["payload"]
    buffer["counter"] += 1

    # Check if we are done with this specific sequence
    total_length = packet_total_length(pgn)
    if len(buffer["payload"]) == total_length:
        final_payload = buffer["payload"]
        del bucket[hashed_id]  # Clean up
        return final_payload[::-1]

    raise MultiPacketInProcessError


def packet_type(pgn: int) -> str:
    """Return the packet type associated with this PGN number

    Args:
        pgn (int): PGN number

    Returns:
        str: Packet type
    """
    return PGN_DB[pgn]["Type"]


def packet_total_length(pgn: int) -> int:
    """Returns the total length of the binary message associated with this PGN number

    Args:
        pgn (int): PGN number

    Returns:
        int: Total length (number of bytes)
    """
    return PGN_DB[pgn]["Length"]


def packet_field_decoder(pgn: int) -> bitstruct.CompiledFormat:
    """Returns a pre-compiled bit field decoder for the message definition
    associated with this PGn number

    Args:
        pgn (int): PGN number

    Returns:
        bitstruct.CompiledFormat: Pre-compiled bit field decoder
    """
    bits = ""
    for field in PGN_DB[pgn]["Fields"]:
        length = field["BitLength"]
        signed = field["Signed"]
        bits = f"{'s' if signed else 'u'}{length}" + bits

    # Bigendian
    bits = ">" + bits

    return bitstruct.compile(bits)


def unpack_fields(pgn: int, data: bytearray) -> dict:
    """Unpack all fields of a complete binary message into a python dictionary

    Args:
        pgn (int): PGN number
        data (bytearray): Complete, raw binary message as a bytearray

    Returns:
        dict: Unpacked fields as a python dictionary
    """

    # Fetch field decoder and unpack raw data
    decoder = packet_field_decoder(pgn)
    # Reverse twice to match field ordering in JSON
    unpacked = decoder.unpack(data[::-1])[::-1]

    output = {}

    for value, field in zip(unpacked, PGN_DB[pgn]["Fields"]):
        # Use field dictionary as blueprint
        tmp = deepcopy(field)

        # Remove uneccessary info without raising any errors
        tmp.pop("BitLength", None)
        tmp.pop("BitOffset", None)
        tmp.pop("BitStart", None)
        tmp.pop("Signed", None)
        tmp.pop("Order", None)
        tmp.pop("Id", None)

        # Add parsed value, scaled according to "Resolution"
        tmp["Value"] = value * (float(tmp.pop("Resolution", 0)) or 1)

        # Add to main dict using Id
        output[field["Id"]] = tmp

    return output


def unpack_complete_message(pgn: int, data: bytearray) -> dict:
    """Unpack a complete n2k message associated with this PGN number

    Args:
        pgn (int): PGN number
        data (bytearray): Complete, raw binary message as a bytearray

    Returns:
        dict: Unpacked message as a python dictionary
    """
    return {
        "Id": PGN_DB[pgn]["Id"],
        "Description": PGN_DB[pgn]["Description"],
        "Fields": unpack_fields(pgn, data),
    }
