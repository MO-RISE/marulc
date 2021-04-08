from pathlib import Path

import pytest

from jasmine import parse_from_iterator
from jasmine.nmea0183 import unpack_nmea_message
from jasmine.exceptions import MultiPacketInProcessError, ParseError
from jasmine.utils import filter_on_talker

THIS_DIR = Path(__file__).parent


def test_unpack_known_regular_nmea_message(pinned):

    assert (
        unpack_nmea_message(
            "$GNGGA,122203.19,5741.1549,N,01153.1748,E,4,37,0.5,4.03,M,35.78,M,,*72"
        )
        == pinned
    )


def test_unpack_known_single_packet_nmea2k_message(pinned):

    assert unpack_nmea_message("$MXPGN,01F200,2856,FFFF7F00000CB201*6F") == pinned


def test_unpack_known_multi_packet_nmea2k_message(pinned):

    multi_packet_message = [
        "$MXPGN,01F201,2838,630D670F50001AA0*17",
        "$MXPGN,01F201,2838,FFFF002D0A3C88A1*12",
        "$MXPGN,01F201,2838,7F0030FFFFFFFFA2*14",
        "$MXPGN,01F201,2738,090800000000A3*69",
    ]

    with pytest.raises(MultiPacketInProcessError):
        unpack_nmea_message(multi_packet_message[0])

    with pytest.raises(MultiPacketInProcessError):
        unpack_nmea_message(multi_packet_message[1])

    with pytest.raises(MultiPacketInProcessError):
        unpack_nmea_message(multi_packet_message[2])

    full_message = unpack_nmea_message(multi_packet_message[3])

    assert full_message == pinned


def test_parse_from_iterator():

    # When parsing using quiet=False, we should receive parsing errors
    with (THIS_DIR / "nmea_test_log.txt").open() as f_handle:
        with pytest.raises(ParseError):
            list(parse_from_iterator(f_handle, quiet=False))

    # When parsing using quiet=True, this should work without raising errors
    with (THIS_DIR / "nmea_test_log.txt").open() as f_handle:
        unpacked = list(parse_from_iterator(f_handle, quiet=True))

        # We should have failed parsing some messages and we will have some
        # multi-packet messages
        assert len(unpacked) < 3000

        # We should have 82 GNGGA messages
        filtered = list(filter_on_talker("GNGGA")(unpacked))
        assert len(filtered) == 82
