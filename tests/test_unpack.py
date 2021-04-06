import pytest

from jasmine.nmea0183 import unpack_nmea_message
from jasmine.exceptions import MultiPacketInProcessError


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
