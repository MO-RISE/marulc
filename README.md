# marulc

**M**aritime **U**npack-**L**ookup-**C**onvert

A library for parsing and unparsing (future feature) of maritime message formats. Currently supports:

    - NMEA0183
    - NMEA2000


Main features:

    - Parsing NMEA0183 sentences to python dictionaries
    - Parsing and decoding NMEA2000 binary messages to python dictionaries
    - Support for NMEA2000 messages wrapped in NMEA0183 sentences (``--PGN``-sentences)
    - Support for multi-packet NMEA2000 messages (fast-type messages)

Since everything is parsed and decoded into regular python dictionaries, serialization to JSON format is very simple.

## Definitions for parsing and decoding
For NMEA0183, definitions have been extracted from the class-based hierarchy of pynmea2 and copmiled into a JSON definition. It can be found [here](https://github.com/RISE-MO/marulc/blob/master/marulc/nmea0183_sentence_formatters.json). The script for extracting these definitions from the pynmea2 source code is available in the ``scripts``-folder.

For NMEA2000, definitions are identical to what is being used in the [CANBOAT](https://github.com/canboat/canboat) project. The definitions can be found [here](https://github.com/RISE-MO/marulc/blob/master/marulc/nmea2000_pgn_specifications.json).

## Installation
From pypi:
```
pip install marulc
```

## Example usage

**Single NMEA0183 sentence using standard sentence library**
```python
from marulc import unpack_nmea0183_message

msg_as_dict = unpack_nmea0183_message("$GNGGA,122203.19,5741.1549,N,01153.1748,E,4,37,0.5,4.03,M,35.78,M,,*72")
```
**Single NMEA0183 sentence wrapping a N2K message using custom formatter**
```python
from marulc import NMEA0183Parser
from marulc.custom_parsers.PCDIN import PCDINFormatter

parser = NMEA0183Parser([PCDINFormatter()])

msg_as_dict = parser.unpack(
    "$PCDIN,01F201,001935D5,38,0000000B0C477CBC0C0000FFFFFFFFFFFF30007F000000000000*26"
)
```

**Parse from iterator**
```python
from marulc import NMEA0183Parser, parse_from_iterator

example_data = [
    "$YDGLL,5741.1612,N,01153.1447,E,110759.00,A,A*6B",
    "$YDRMC,110759.00,A,5741.1612,N,01153.1447,E,0.0,300.0,010170,,E,A,C*72",
    "$YDRPM,E,0,0.0,,A*64",
    "$YDRPM,E,1,0.0,,A*65",
    "$YDROT,-0.6,A*10",
    "$YDHDG,0.0,0.0,E,,*3F",
    "$YDHDM,0.0,M*3F",
    "$YDRSA,-0.1,A,,V*48",
    "$YDVTG,328.0,T,328.0,M,0.0,N,0.0,K,A*29"
]

parser = NMEA0183Parser()

for unpacked_msg in parse_from_iterator(parser, example_data, quiet=True):
    print(unpacked_msg)
```

**NMEA2000 frames**
```python
from marulc import NMEA2000Parser

parser = NMEA2000Parser()

# Unpack a single frame message
# Note: This will only work for single-frame N2K messages. For multi-frame messages, the unpack
# method will raise a `MultiPacketInProcessError` and expect further frames to be provided
msg_as_dict = parser.unpack("09F10D0A FF 00 00 00 FF 7F FF FF")

# For unpacking multi-frame messages, its usually better to use a `parse_from_iterator` setup, such as:
from marulc import parse_from_iterator

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
from marulc import NMEA0183Parser, parse_from_iterator
from marulc.utils import filter_on_talker_formatter

example_data = [
    "$YDGLL,5741.1612,N,01153.1447,E,110759.00,A,A*6B",
    "$YDRMC,110759.00,A,5741.1612,N,01153.1447,E,0.0,300.0,010170,,E,A,C*72",
    "$YDRPM,E,0,0.0,,A*64",
    "$YDRPM,E,1,0.0,,A*65",
    "$YDROT,-0.6,A*10",
    "$YDHDG,0.0,0.0,E,,*3F",
    "$YDHDM,0.0,M*3F",
    "$YDRSA,-0.1,A,,V*48",
    "$YDVTG,328.0,T,328.0,M,0.0,N,0.0,K,A*29"
]

parser = NMEA0183Parser()

iterator_all = parse_from_iterator(parser, example_data, quiet=True)

rpm_sentences = list(filter(filter_on_talker_formatter("..RPM"), iterator_all))
assert len(rpm_sentences) == 2
```

**Extract specific value from specific messages**
```python
from marulc import NMEA2000Parser, parse_from_iterator
from marulc.utils import filter_on_pgn, deep_get

example_data = [
    "08FF12C9 4A 9A 00 17 DB 00 00 00",
    "08FF13C9 4A 9A 00 00 FF FF FF FF",
    "08FF14C9 4A 9A 00 00 00 00 00 FF",
    "09F200C9 00 57 30 FF FF 01 FF FF",
    "09F205C9 00 FC FF FF FF FF 00 FF",
    "09F10DE5 00 F8 FF 7F F9 FE FF FF",
    "09F11365 DA AB 4B FE FF FF FF FF",
    "08FF12B7 4A 9A 01 17 DB 00 00 00",
    "08FF13B7 4A 9A 01 00 FF FF FF FF",
    "08FF14B7 4A 9A 01 00 00 00 00 FF",
    "09F200B7 01 DA 2F FF FF 01 FF FF",
    "09F205B7 01 FC FF FF FF FF 00 FF",
]

parser = NMEA2000Parser()

iterator_all = parse_from_iterator(parser, example_data, quiet=True)

speeds = []
for filtered_unpacked_msg in filter(filter_on_pgn(127488), iterator_all):
    speed = deep_get(filtered_unpacked_msg, "Fields", "speed")
    speeds.append(speed)

assert len(speeds) == 2
```

**Extraction using JSON pointers**
Requires the `jsonpointer` package (`pip install jsonpointer`)
```python
from jsonpointer import resolve_pointer

from marulc import NMEA2000Parser, parse_from_iterator
from marulc.utils import filter_on_pgn, deep_get

example_data = [
    "08FF12C9 4A 9A 00 17 DB 00 00 00",
    "08FF13C9 4A 9A 00 00 FF FF FF FF",
    "08FF14C9 4A 9A 00 00 00 00 00 FF",
    "09F200C9 00 57 30 FF FF 01 FF FF",
    "09F205C9 00 FC FF FF FF FF 00 FF",
    "09F10DE5 00 F8 FF 7F F9 FE FF FF",
    "09F11365 DA AB 4B FE FF FF FF FF",
    "08FF12B7 4A 9A 01 17 DB 00 00 00",
    "08FF13B7 4A 9A 01 00 FF FF FF FF",
    "08FF14B7 4A 9A 01 00 00 00 00 FF",
    "09F200B7 01 DA 2F FF FF 01 FF FF",
    "09F205B7 01 FC FF FF FF FF 00 FF",
]

parser = NMEA2000Parser()

iterator_all = parse_from_iterator(parser, example_data, quiet=True)

speeds = []
for filtered_unpacked_msg in filter(filter_on_pgn(127488), iterator_all):
    speed = resolve_pointer(filtered_unpacked_msg, "/Fields/speed")
    speeds.append(speed)

assert len(speeds) == 2
```

## Development setup
Create a virtual environment:

    python3 -m venv venv
    source venv/bin/activate

Install the development requirements:

    pip install -r requirements.txt

Run the formatter and linter:

    black marulc tests
    pylint marulc

Run the tests:

    pytest --codeblocks
