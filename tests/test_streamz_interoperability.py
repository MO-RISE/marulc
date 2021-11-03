from pathlib import Path

from streamz import Stream

from jasmine import unpack_nmea0183_message
from jasmine.utils import filter_on_talker_formatter

THIS_DIR = Path(__file__).parent


def quiet_unpack(*args, **kwargs):
    try:
        return unpack_nmea0183_message(*args, **kwargs)
    except Exception:
        pass


def test_unpacking_with_pipeline():
    # Define pipeline
    source: Stream = Stream()
    unpacked = source.map(quiet_unpack).filter(lambda unpacked: unpacked is not None)
    vtg_messages = unpacked.filter(filter_on_talker_formatter("..VTG")).sink_to_list()
    gga_messages = unpacked.filter(filter_on_talker_formatter("..GGA")).sink_to_list()

    with (THIS_DIR / "nmea_test_log.txt").open() as f_handle:
        for line in f_handle:
            source.emit(line)

    assert len(vtg_messages) == 174
    assert len(gga_messages) == 87
