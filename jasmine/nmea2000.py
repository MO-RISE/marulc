import json
from pathlib import Path
from copy import deepcopy
from binascii import unhexlify

import bitstruct

from jasmine.exceptions import (
    MultiPacketDiscardedError,
    MultiPacketInProcessError,
    PGNError,
)

# Read PGNs metadata from CANBOAT database
DB_PATH = Path(__file__).parent / "pgns.json"
with DB_PATH.open() as f_handle:
    PGN_DB = {item["PGN"]: item for item in json.load(f_handle)["PGNs"]}

# Fast packet buffer to deal with multi-sentence messages
BUCKET = dict()


def process_sub_packet(pgn: int, address: int, data: bytearray):
    """
    /*
    * NMEA 2000 uses the 8 'data' bytes as follows for fast packet type:
    * data[0] is an 'order' that increments, or not (depending a bit on implementation).
    * If the size of the packet <= 7 then the data follows in data[1..7]
    * If the size of the packet > 7 then the next byte data[1] is the size of the payload
    * and data[0] is divided into 5 bits index into the fast packet, and 3 bits 'order
    * that increases.
    * This means that for 'fast packets' the first bucket (sub-packet) contains 6 payload
    * bytes and 7 for remaining. Since the max index is 31, the maximal payload is
    * 6 + 31 * 7 = 223 bytes
    */
    """
    length = len(data) * 8  # bits
    order, idx = bitstruct.unpack(f">P{length - 8}u3u5", data)
    hashed_id = hash((pgn, address, order))

    # Too late to the party
    if idx > 0 and hashed_id not in BUCKET:
        raise MultiPacketDiscardedError

    # First message in a new sequence
    if idx == 0:
        (payload,) = bitstruct.unpack(">r48P16", data)
        BUCKET[hashed_id] = {"payload": payload, "counter": 1}
        raise MultiPacketInProcessError

    # Fetch existing bucket
    bucket = BUCKET[hashed_id]

    # Check for fck-up
    if bucket["counter"] != idx:
        # Dropped sub-package
        del BUCKET[hashed_id]
        raise MultiPacketDiscardedError

    # Still on track, append this payload to existing one!
    (payload,) = bitstruct.unpack(f">r{length - 8}P8", data)
    bucket["payload"] = payload + bucket["payload"]
    bucket["counter"] += 1

    # Check if we are done with this specific sequence
    total_length = packet_total_length(pgn)
    if len(bucket["payload"]) == total_length:
        final_payload = bucket["payload"]
        del BUCKET[hashed_id]  # Clean up
        return final_payload


def packet_type(pgn: int) -> str:
    return PGN_DB[pgn]["Type"]


def packet_total_length(pgn: int) -> int:
    return PGN_DB[pgn]["Length"]


def packet_field_decoder(pgn: int):
    bits = ""
    for field in PGN_DB[pgn]["Fields"]:
        length = field["BitLength"]
        signed = field["Signed"]
        bits = f"{'s' if signed else 'u'}{length}" + bits

    # Bigendian
    bits = ">" + bits

    return bitstruct.compile(bits)


def unpack_fields(pgn: int, data: bytearray) -> dict:

    # Fetch field decoder and unpack raw data
    decoder = packet_field_decoder(pgn)
    unpacked = decoder.unpack(data)[::-1]  # Reverse to match field ordering in JSON

    output = {}

    for value, field in zip(unpacked, PGN_DB[pgn]["Fields"]):
        # Use field dictionary as blueprint
        tmp = {}
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
    return {
        "Id": PGN_DB[pgn]["Id"],
        "Description": PGN_DB[pgn]["Description"],
        "Fields": unpack_fields(pgn, data),
    }


def unpack_PGN_message(msg: list) -> dict:
    """
    Decode --PGN sentence according to
    https://opencpn.org/wiki/dokuwiki/lib/exe/fetch.php?media=opencpn:software:mxpgn_sentence.pdf
    """
    # Unpack pgn
    pgn = int(msg[0], 16)

    if pgn not in PGN_DB or not PGN_DB[pgn]["Complete"]:
        raise PGNError(f"Cant decode message with PGN {pgn}", msg)

    # Unpack attributes
    _, priority, dlc, address = bitstruct.unpack(">u1u3u4u8", unhexlify(msg[1]))

    # Unpack message
    if packet_type(pgn) == "Single":
        output = unpack_complete_message(pgn, unhexlify(msg[2]))
    elif packet_type(pgn) == "Fast":
        # Will raise if packet is not complete!
        complete_packet = process_sub_packet(pgn, address, unhexlify(msg[2]))
        output = unpack_complete_message(pgn, complete_packet)

    else:
        raise PGNError(f"Cant decode message with PGN {pgn}", msg)

    # Add some attributes to output
    output["Priority"] = priority
    output["Address"] = address
    output["PGN"] = pgn

    return output
