"""Package for parsing/decoding NMEA0183 and NMEA2000 messages
"""
from jasmine.nmea0183 import unpack_nmea0183_message, NMEA0183Parser
from jasmine.utils import parse_from_iterator
