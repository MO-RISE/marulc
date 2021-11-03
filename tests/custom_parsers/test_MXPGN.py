from binascii import unhexlify

import pytest

from jasmine.nmea2000 import unpack_complete_message
from jasmine.custom_parsers.MXPGN import MXPGNFormatter
from jasmine.exceptions import (
    PGNError,
)


def test_correct_sentence_formatter():
    assert "PGN" == MXPGNFormatter().sentence_formatter()


def test_unpack_PGN_message_correct():
    raw = unhexlify("00000024047FFFFF")
    textual = ["01F200", "2838", "00000024047FFFFF"]

    msg = MXPGNFormatter().unpack(textual)

    assert unpack_complete_message(127488, raw).items() <= msg.items()

    assert msg["Fields"]["speed"] == 0.0

    assert msg["PGN"] == 127488
    assert msg["Priority"] == 2
    assert msg["SourceAddress"] == 56


def test_reversal_of_byte_ordering():

    textual1 = ["01F200", "2838", "FFFF7F00000CB201"]
    textual2 = ["01F200", "2838", "01B20C00007FFFFF"]

    msg1 = MXPGNFormatter().unpack(textual1)
    msg2 = MXPGNFormatter(reverse_byte_ordering=True).unpack(textual2)

    assert msg1 == msg2


def test_unpack_PGN_message_wrong_PGN():
    textual = ["01F256", "2856", "FFFF7F00000CB201"]

    with pytest.raises(PGNError):
        MXPGNFormatter().unpack(textual)
