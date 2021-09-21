# jasmine

A parser for NMEA 0183 and 2000 messages, heavily inspired by [pynmea2](https://github.com/Knio/pynmea2).

Main features:

* Parsing NMEA0183 sentences to python dictionaries
* Parsing and decoding NMEA2000 binary messages to python dictionaries
* Support for NMEA2000 messages wrapped in NMEA0183 sentences (``--PGN``-sentences)
* Support for multi-packet NMEA2000 messages (fast-type messages)

Since everything is parsed and decoded into regular python dictionaries, serialization to JSON format is very simple.

For parsing and decoding of messages, the following definitions are used:

- For NMEA0183, definitions have been extracted from the class-based hierarchy of pynmea2 and copmiled into a JSON definition. It can be found [here](https://github.com/RISE-MO/jasmine/blob/master/jasmine/nmea0183_sentence_formatters.json). The script for extracting these definitions from the pynmea2 source code is available in the ``scripts``-folder
- For NMEA2000, definitions are identical to what is being used in the [CANBOAT](https://github.com/canboat/canboat) project. The definitions can be found [here](https://github.com/RISE-MO/jasmine/blob/master/jasmine/nmea2000_pgn_specifications.json)

## Installation
From morise pypi-server:
```
pip install morise-jasmine
```

Note: Requires your pip installation to be configured accordingly!

## Example usage

**Single NMEA0183 sentence using standard sentence library**
```python
from jasmine import unpack_nmea0183_message

msg_as_dict = unpack_nmea0183_message("$GNGGA,122203.19,5741.1549,N,01153.1748,E,4,37,0.5,4.03,M,35.78,M,,*72")
```
**Single NMEA0183 sentence wrapping a N2K message using custom formatter**
```python
from jasmine import NMEA0183Parser
from jasmine.custom_parsers.PCDIN import PCDINFormatter

parser = NMEA0183Parser([PCDINFormatter()])

msg_as_dict = parser.unpack(
    "$PCDIN,01F201,001935D5,38,0000000B0C477CBC0C0000FFFFFFFFFFFF30007F000000000000*26"
)
```

**Parse from iterator**
```python
from jasmine import NMEA0183Parser, parse_from_iterator

parser = NMEA0183Parser()

with open("nmea_log.txt") as f_handle:
    for unpacked_msg in parse_from_iterator(parser, f_handle, quiet=True):
        print(unpacked_msg)
```

**NMEA2000 frames**
```python
from jasmine import NMEA2000Parser

parser = NMEA2000Parser()

# Unpack a single frame message
# Note: This will only work for single-frame N2K messages. For multi-frame messages, the unpack
# method will raise a `MultiPacketInProcessError` and expect further frames to be provided
msg_as_dict = parser.unpack("09F10D0A FF 00 00 00 FF 7F FF FF")

# For unpacking multi-frame messages, its usually better to use a `parse_from_iterator` setup, such as:
from jasmine import parse_from_iterator

multi_frame_message = [
    "09F201B7 C0 1A 01 FF FF FF FF B0",
    "09F201B7 C1 81 3C 05 00 00 B0 BA",
    "09F201B7 C2 1C 00 FF FF FF FF FF",
    "09F201B7 C3 00 00 00 00 7F 7F FF",
]

for full_message in parse_from_iterator(parser, multi_frame_message, quiet=True):
    print(full_message)

```

**Filter for specific messages**
```python
from jasmine import NMEA0183Parser, parse_from_iterator
from jasmine.utils import filter_on_talker_formatter

parser = NMEA0183Parser()

with open("nmea0183_log.txt") as f_handle:
    iterator_all = parse_from_iterator(parser, f_handle, quiet=True):

    for filtered_unpacked_msg in filter_on_talker_formatter("..GGA")(iterator_all): # Accepts regex!
        print(filtered_unpacked_msg)
```

**Extract specific value from specific messages**
```python
from jasmine import NMEA2000Parser, parse_from_iterator
from jasmine.utils import filter_on_pgn, deep_get

parser = NMEA2000Parser()

with open("nmea2000_log.txt") as f_handle:
    iterator_all = parse_from_iterator(parser, f_handle, quiet=True):

    for filtered_unpacked_msg in filter_on_pgn(127488)(iterator_all):
        speed = deep_get(filtered_unpacked_msg, "Fields", "speed")
        print(f"Engine running speed: {speed['Value']} {speed['Units']}")
```

**Extraction using JSON pointers**
Requires the `jsonpointer` package (`pip install jsonpointer`)
```python
from jsonpointer import resolve_pointer

from jasmine import NMEA2000Parser, parse_from_iterator
from jasmine.utils import filter_on_pgn, deep_get

parser = NMEA2000Parser()

with open("nmea2000_log.txt") as f_handle:
    iterator_all = parse_from_iterator(f_handle, quiet=True):

    for filtered_unpacked_msg in filter_on_pgn(127488)(iterator_all):
        speed = resolve_pointer(filtered_unpacked_msg, "/Fields/speed")
        print(f"Engine running speed: {speed['Value']} {speed['Units']}")
```

