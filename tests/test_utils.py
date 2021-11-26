from marulc.utils import deep_get, filter_on_pgn, filter_on_talker_formatter


def fake_iterator():
    yield {"Talker": "GN", "Formatter": "GGA"}
    yield {"Talker": "GN", "Formatter": "GGA"}
    yield {"Talker": "GN", "Formatter": "VTG"}
    yield {"Talker": "PASHR", "Formatter": ""}
    yield {"Talker": "MX", "Formatter": "PGN", "PGN": 127488}
    yield {"Talker": "MX", "Formatter": "PGN", "PGN": 127488}
    yield {"Talker": "MX", "Formatter": "PGN", "PGN": 127489}


def test_deep_get():
    d = {"A": {"B": {"C": 3, "C2": 0}}}
    assert deep_get(d) == d
    assert deep_get(d, "A", "B", "C") == 3
    assert deep_get(d, "A", "B", "C2") == 0
    assert deep_get(d, "A", "B", "C", "D") is None
    assert deep_get(d, "A", "B", "C", "D", default=89) == 89


def test_filter_on_address():
    filtered = list(filter(filter_on_talker_formatter("GNGGA"), fake_iterator()))
    assert len(filtered) == 2

    filtered = list(
        filter(filter_on_talker_formatter("..GGA", "PASHR"), fake_iterator())
    )
    assert len(filtered) == 3


def test_filter_on_PGN():
    filtered = list(filter(filter_on_pgn(127488), fake_iterator()))
    assert len(filtered) == 2

    filtered = list(filter(filter_on_pgn(127488, 127489), fake_iterator()))
    assert len(filtered) == 3


def test_filter_chaining():
    filtered = list(
        filter(
            filter_on_talker_formatter("GN..."),
            filter(filter_on_talker_formatter("...G."), fake_iterator()),
        )
    )
    assert len(filtered) == 2
