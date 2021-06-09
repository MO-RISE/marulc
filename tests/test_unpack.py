from pathlib import Path

import pytest

from jasmine import parse_from_iterator, NMEA0183Parser, unpack_nmea0183_message
from jasmine.exceptions import MultiPacketInProcessError, ParseError
from jasmine.utils import filter_on_talker_formatter, filter_on_pgn, deep_get
from jasmine.custom_parsers.MXPGN import MXPGNFormatter
from jasmine.custom_parsers.PCDIN import PCDINFormatter

THIS_DIR = Path(__file__).parent


def test_unpack_known_regular_nmea_message(pinned):

    assert (
        unpack_nmea0183_message(
            "$GNGGA,122203.19,5741.1549,N,01153.1748,E,4,37,0.5,4.03,M,35.78,M,,*72"
        )
        == pinned
    )


def test_unpack_known_single_packet_nmea2k_message(pinned):

    parser = NMEA0183Parser([MXPGNFormatter()])

    assert parser.unpack("$MXPGN,01F200,2856,01B20C00007FFFFF*6F") == pinned


def test_unpack_known_multi_packet_nmea2k_message(pinned):

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


def test_parse_from_iterator(pinned):

    parser = NMEA0183Parser([MXPGNFormatter(), PCDINFormatter()])

    # When parsing using quiet=False, we should receive parsing errors
    with (THIS_DIR / "nmea_test_log.txt").open() as f_handle:
        with pytest.raises(ParseError):
            list(parse_from_iterator(parser, f_handle, quiet=False))

    # When parsing using quiet=True, this should work without raising errors
    with (THIS_DIR / "nmea_test_log.txt").open() as f_handle:
        unpacked = list(parse_from_iterator(parser, f_handle, quiet=True))

        # We should have failed parsing some messages and we will have some
        # multi-packet messages
        assert len(unpacked) < 3000

        # We should have 174 ..VTG messages
        filtered = list(filter_on_talker_formatter("..VTG")(unpacked))
        assert len(filtered) == 174

    # Lets try to extract a timeserie
    with (THIS_DIR / "nmea_test_log.txt").open() as f_handle:
        rpms = [
            deep_get(msg, "Fields", "speed", "Value")
            for msg in filter_on_pgn(127488)(
                parse_from_iterator(parser, f_handle, quiet=True)
            )
        ]

        assert rpms == pinned
