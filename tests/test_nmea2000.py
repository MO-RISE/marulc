from binascii import unhexlify

import pytest

from jasmine.nmea2000 import (
    packet_type,
    packet_total_length,
    packet_field_decoder,
    unpack_fields,
    unpack_complete_message,
    unpack_PGN_message,
    process_sub_packet,
    BUCKET,
)
from jasmine.exceptions import (
    PGNError,
    ParseError,
    MultiPacketDiscardedError,
    MultiPacketInProcessError,
)


@pytest.fixture
def clean_bucket():
    BUCKET.clear()
    yield


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
    assert unpack_fields(127488, unhexlify("FFFF7F00000CB201")) == pinned


def test_unpack_complete_message(pinned):
    raw = unhexlify("FFFF7F00000CB201")
    msg = unpack_complete_message(127488, raw)

    assert msg["Fields"] == unpack_fields(127488, raw)

    assert msg == pinned


def test_unpack_PGN_message_correct():
    raw = unhexlify("FFFF7F00000CB201")
    textual = ["01F200", "2856", "FFFF7F00000CB201"]

    msg = unpack_PGN_message(textual)

    assert unpack_complete_message(127488, raw).items() <= msg.items()

    assert msg["PGN"] == 127488
    assert msg["Priority"] == 2
    assert msg["Address"] == 86


def test_unpack_PGN_message_wrong_PGN():
    textual = ["01F256", "2856", "FFFF7F00000CB201"]

    with pytest.raises(PGNError):
        unpack_PGN_message(textual)


def test_process_subpacket_first_message(clean_bucket):
    raw = unhexlify("630D670F50001AA0")

    with pytest.raises(MultiPacketInProcessError):
        process_sub_packet(127489, 86, raw)

    assert len(BUCKET) == 1
    assert list(BUCKET.values())[0]["counter"] == 1


def test_process_subpacket_second_message(clean_bucket):
    raw = unhexlify("FFFF002D0A3C88A1")

    # Trying to parse the second message in a sequence without having
    # received the first message will fail
    with pytest.raises(MultiPacketDiscardedError):
        process_sub_packet(127489, 86, raw)


def test_process_subpacket_first_third_message(clean_bucket):
    raw = unhexlify("630D670F50001AA0")

    with pytest.raises(MultiPacketInProcessError):
        process_sub_packet(127489, 86, raw)

    raw = unhexlify("7F0030FFFFFFFFA2")

    with pytest.raises(MultiPacketDiscardedError):
        process_sub_packet(127489, 86, raw)
