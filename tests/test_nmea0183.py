import pytest

from jasmine.nmea0183 import (
    calculate_checksum,
    parse_value,
    unpack_using_formatter,
    unpack_using_proprietary,
    get_description_for_sentence_formatter,
)


def test_checksum():
    nmea_str = "GNGGA,122203.19,5741.1549,N,01153.1748,E,4,37,0.5,4.03,M,35.78,M,,"
    checksum = "72"

    assert calculate_checksum(nmea_str) == int(checksum, 16)


def test_parse_value():
    assert type(parse_value("12.353")) == float
    assert type(parse_value("12.0")) == int
    assert type(parse_value("12")) == int
    assert type(parse_value("12h")) == str


def test_unpack_using_talker(pinned):
    data = [
        "122203.19",
        "5741.1549",
        "N",
        "01153.1748",
        "E",
        "4",
        "37",
        "0.5",
        "4.03",
        "M",
        "35.78",
        "M",
        "",
        "",
    ]
    msg = unpack_using_formatter("GGA", data)
    assert msg == pinned


def test_get_description(pinned):
    assert get_description_for_sentence_formatter("RPM") == pinned

    with pytest.raises(ValueError):
        get_description_for_sentence_formatter("muppet")


@pytest.mark.skip("Find a reasonable example")
def test_unpack_proprietary(pinned):
    pass
