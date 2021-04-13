# jasmine

A parser for NMEA 0183 and 2000 messages, heavily inspired by [pynmea2](https://github.com/Knio/pynmea2).

Main features:

* Parsing NMEA0183 sentences to python dictionaries
* Parsing and decoding NMEA2000 binary messages to python dictionaries
* Support for NMEA2000 messages wrapped in NMEA0183 sentences (``--PGN``-sentences)
* Support for multi-packet NMEA2000 messages (fast-type messages)

Since everything is parsed and decoded into regular python dictionaries, serialization to JSON format is very simple.

For parsing and decoding of messages, the following definitions are used:

- For NMEA0183, definitions have been extracted from the class-based hierarchy of pynmea2 and copmiled into a JSON definition. It can be found [here](https://github.com/RISE-MO/jasmine/blob/master/jasmine/talkers.json). The script for extracting these definitions from the pynmea2 source code is available in the ``scripts``-folder
- For NMEA2000, definitions are identical to what is being used in the [CANBOAT](https://github.com/canboat/canboat) project. The definitions can be found [here](https://github.com/RISE-MO/jasmine/blob/master/jasmine/pgns.json)

## Example usage

**Single sentence**
```python
from jasmine import unpack_nmea_message

msg_as_dict = unpack_nmea_message("$GNGGA,122203.19,5741.1549,N,01153.1748,E,4,37,0.5,4.03,M,35.78,M,,*72")
```

**Parse from iterator**
```python
from jasmine import parse_from_iterator

with open("nmea_log.txt") as f_handle:
    for unpacked_msg in parse_from_iterator(f_handle, quiet=True):
        print(unpacked_msg)
```

**Filter for specific messages**
```python
from jasmine import parse_from_iterator
from jasmine.utils import filter_on_talker

with open("nmea_log.txt") as f_handle:
    iterator_all = parse_from_iterator(f_handle, quiet=True):

    for filtered_unpacked_msg in filter_on_talker("..GGA")(iterator_all): # Accepts regex!
        print(filtered_unpacked_msg)
```

**Extract specific value from specific messages**
```python
from jasmine import parse_from_iterator
from jasmine.utils import filter_on_pgn, deep_get

with open("nmea_log.txt") as f_handle:
    iterator_all = parse_from_iterator(f_handle, quiet=True):

    for filtered_unpacked_msg in filter_on_pgn(127488)(iterator_all):
        speed = deep_get(filtered_unpacked_msg, "Fields", "speed")
        print(f"Engine running speed: {speed['Value']} {speed['Units']}")
```
