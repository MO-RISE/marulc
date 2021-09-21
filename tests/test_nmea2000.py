from binascii import unhexlify

import pytest

from jasmine.nmea2000 import (
    unpack_header,
    packet_type,
    packet_total_length,
    packet_field_decoder,
    unpack_fields,
    unpack_complete_message,
    process_sub_packet,
    get_description_for_pgn,
)
from jasmine.exceptions import (
    MultiPacketDiscardedError,
    MultiPacketInProcessError,
)


def test_unpack_header():

    ## Rudder message
    sa, pgn, prio = unpack_header(unhexlify("09F10DE5"))
    assert sa == 229
    assert pgn == 127245
    assert prio == 2

    ## Small craft status
    sa, pgn, prio = unpack_header(unhexlify("09FE1065"))
    assert sa == 101
    assert pgn == 130576
    assert prio == 2

    ## Engine Parameters, Rapid Update
    sa, pgn, prio = unpack_header(unhexlify("09F200B7"))
    assert sa == 183
    assert pgn == 127488
    assert prio == 2


def test_packet_type():
    assert packet_type(127488) == "Single"
    assert packet_type(127489) == "Fast"


def test_packet_total_length():
    assert packet_total_length(127488) == 8
    assert packet_total_length(127489) == 26


def test_packet_field_decoder():
    assert packet_field_decoder(127488).calcsize() == 8 * 8
    assert packet_field_decoder(127489).calcsize() == 8 * 26


def test_unpack_fields(pinned):
    assert unpack_fields(127488, unhexlify("01B20C00007FFFFF")) == pinned


def test_unpack_complete_message(pinned):
    raw = unhexlify("01B20C00007FFFFF")
    msg = unpack_complete_message(127488, raw)

    assert msg["Fields"] == unpack_fields(127488, raw)

    assert msg == pinned


def test_process_subpacket_first_message(clean_bucket):
    raw = unhexlify("A01A00500F670D63")

    with pytest.raises(MultiPacketInProcessError):
        process_sub_packet(127489, 86, raw, clean_bucket)

    assert len(clean_bucket) == 1
    assert list(clean_bucket.values())[0]["counter"] == 1


def test_process_subpacket_second_message(clean_bucket):
    raw = unhexlify("A1883C0A2D00FFFF")

    # Trying to parse the second message in a sequence without having
    # received the first message will fail
    with pytest.raises(MultiPacketDiscardedError):
        process_sub_packet(127489, 86, raw, clean_bucket)


def test_process_subpacket_first_third_message(clean_bucket):
    raw = unhexlify("A01A00500F670D63")

    with pytest.raises(MultiPacketInProcessError):
        process_sub_packet(127489, 86, raw, clean_bucket)

    raw = unhexlify("A2FFFFFFFF30007F")

    with pytest.raises(MultiPacketDiscardedError):
        process_sub_packet(127489, 86, raw, clean_bucket)


def test_get_description(pinned):
    assert get_description_for_pgn(127489) == pinned

    with pytest.raises(ValueError):
        get_description_for_pgn(372418338952)
