from pathlib import Path

import pytest

from marulc import (
    parse_from_iterator,
    NMEA0183Parser,
    unpack_nmea0183_message,
    NMEA2000Parser,
)
from marulc.exceptions import MultiPacketInProcessError, ParseError
from marulc.utils import filter_on_talker_formatter, filter_on_pgn, deep_get
from marulc.custom_parsers.MXPGN import MXPGNFormatter
from marulc.custom_parsers.PCDIN import PCDINFormatter

THIS_DIR = Path(__file__).parent


def test_unpack_known_regular_nmea_message(pinned):

    assert (
        unpack_nmea0183_message(
            "$GNGGA,122203.19,5741.1549,N,01153.1748,E,4,37,0.5,4.03,M,35.78,M,,*72"
        )
        == pinned
    )


def test_unpack_MXPGN_single_packet_nmea2k_message(pinned):

    parser = NMEA0183Parser([MXPGNFormatter()])

    assert parser.unpack("$MXPGN,01F200,2856,01B20C00007FFFFF*6F") == pinned


def test_unpack_MXPGN_multi_packet_nmea2k_message(pinned):

    parser = NMEA0183Parser([MXPGNFormatter()])

    multi_packet_message = [
        "$MXPGN,01F201,2838,A01A00500F670D63*17",
        "$MXPGN,01F201,2838,A1883C0A2D00FFFF*12",
        "$MXPGN,01F201,2838,A2FFFFFFFF30007F*14",
        "$MXPGN,01F201,2738,A3000000000809*69",
    ]

    with pytest.raises(MultiPacketInProcessError):
        parser.unpack(multi_packet_message[0])

    with pytest.raises(MultiPacketInProcessError):
        parser.unpack(multi_packet_message[1])

    with pytest.raises(MultiPacketInProcessError):
        parser.unpack(multi_packet_message[2])

    full_message = parser.unpack(multi_packet_message[3])

    assert full_message == pinned


def test_unpack_PCDIN_packet_nmea2k_message(pinned):

    parser = NMEA0183Parser([PCDINFormatter()])

    msg = parser.unpack(
        "$PCDIN,01F201,001935D5,38,0000000B0C477CBC0C0000FFFFFFFFFFFF30007F000000000000*26"
    )

    assert msg == pinned


def test_parse_from_iterator(pinned):

    parser = NMEA0183Parser([MXPGNFormatter(), PCDINFormatter()])

    with (THIS_DIR / "nmea_test_log.txt").open() as f_handle:
        unpacked = list(parse_from_iterator(parser, f_handle, quiet=False))

        # We should have 174 ..VTG messages
        filtered = list(filter(filter_on_talker_formatter("..VTG"), unpacked))
        assert len(filtered) == 174

    # Lets try to extract a timeserie
    with (THIS_DIR / "nmea_test_log.txt").open() as f_handle:
        rpms = [
            deep_get(msg, "Fields", "speed", "Value")
            for msg in filter(
                filter_on_pgn(127488), parse_from_iterator(parser, f_handle, quiet=True)
            )
        ]

        assert rpms == pinned


def test_unpack_N2K_single_frame_message(pinned):

    parser = NMEA2000Parser()

    single_frame_message = "09F10D0A FF 00 00 00 FF 7F FF FF"

    parsed = parser.unpack(single_frame_message)

    assert parsed == pinned


def test_unpack_N2K_multi_frame_message(pinned):

    parser = NMEA2000Parser()

    multi_packet_message = [
        "09F201B7 C01A01FFFFFFFFB0",
        "09F201B7 C1813C050000B0BA",
        "09F201B7 C21C00FFFFFFFFFF",
        "09F201B7 C3000000007F7FFF",
    ]

    with pytest.raises(MultiPacketInProcessError):
        parser.unpack(multi_packet_message[0])

    with pytest.raises(MultiPacketInProcessError):
        parser.unpack(multi_packet_message[1])

    with pytest.raises(MultiPacketInProcessError):
        parser.unpack(multi_packet_message[2])

    full_message = parser.unpack(multi_packet_message[3])

    assert full_message == pinned
