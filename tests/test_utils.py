import pytest
from jasmine.utils import deep_get, filter_on_pgn, filter_on_talker


def fake_iterator():
    yield {"Talker": "GNGGA"}
    yield {"Talker": "GNGGA"}
    yield {"Talker": "GNVTG"}
    yield {"Talker": "PASHR"}
    yield {"Talker": "MXPGN", "PGN": 127488}
    yield {"Talker": "MXPGN", "PGN": 127488}
    yield {"Talker": "MXPGN", "PGN": 127489}


def test_deep_get():
    d = {"A": {"B": {"C": 3}}}
    assert deep_get(d) == d
    assert deep_get(d, "A", "B", "C") == 3
    assert deep_get(d, "A", "B", "C", "D") is None
    assert deep_get(d, "A", "B", "C", "D", default=89) == 89


def test_filter_on_talker():
    filtered = list(filter_on_talker("GNGGA")(fake_iterator()))
    assert len(filtered) == 2

    filtered = list(filter_on_talker("..GGA", "PASHR")(fake_iterator()))
    assert len(filtered) == 3


def test_filter_on_PGN():
    filtered = list(filter_on_pgn(127488)(fake_iterator()))
    assert len(filtered) == 2

    filtered = list(filter_on_pgn(127488, 127489)(fake_iterator()))
    assert len(filtered) == 3


def test_filter_chaining():
    filtered = list(
        filter_on_talker("GN...")(filter_on_talker("...G.")(fake_iterator()))
    )
    assert len(filtered) == 2
