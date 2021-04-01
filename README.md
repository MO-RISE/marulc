# jasmine

A parser for NMEA 0183 and 2000 messages

Heavily inspired by [pynmea2](https://github.com/Knio/pynmea2) but reworked quite a lot to allow for supporting:
* Easy serialization
* PGN sentences
* Multi-packet sentences

Definitions for parsing sentence have been compiled from
* NMEA0183 messages: Using the definitions provided by pynmea2
* NMEA2000 messages: Using the deinfitions provided by CANBOAT

## Example usage

See tests for now


## ToDo:

- [ ] Linting
- [ ] Test coverage
- [ ] Documentation
- [ ] Helper function for streaming input (basically support any kind of stream that yields strings with NMEA messages)
- [ ] Helper functions for extracting timeseries. (I.e converting from array of structs to structs of arrays)
