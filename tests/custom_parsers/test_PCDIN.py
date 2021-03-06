from binascii import unhexlify

import pytest

from marulc.nmea2000 import unpack_complete_message
from marulc.custom_parsers.PCDIN import PCDINFormatter
from marulc.exceptions import (
    PGNError,
)


def test_correct_sentence_formatter():
    assert "CDI" == PCDINFormatter().manufacturer_code()


def test_unpack_PGN_message_correct():
    raw = unhexlify("0000000B0C477CBC0C0000FFFFFFFFFFFF30007F000000000000")
    textual = [
        "N",
        "01F201",
        "001935D5",
        "38",
        "0000000B0C477CBC0C0000FFFFFFFFFFFF30007F000000000000",
    ]

    msg = PCDINFormatter().unpack(textual)
    print(msg)

    assert unpack_complete_message(127489, raw).items() <= msg.items()

    assert msg["PGN"] == 127489
    assert msg["SourceID"] == 56


def test_unpack_PGN_message_wrong_PGN():
    textual = ["N", "01F256", "2856", "FFFF7F00000CB201"]

    with pytest.raises(PGNError):
        PCDINFormatter().unpack(textual)
