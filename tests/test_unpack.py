from jasmine.nmea0183 import unpack_nmea_message


def test_unpack_single_known_message(pinned):

    assert (
        unpack_nmea_message(
            "$GNGGA,122203.19,5741.1549,N,01153.1748,E,4,37,0.5,4.03,M,35.78,M,,*72"
        )
        == pinned
    )
