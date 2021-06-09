from typing import List
from binascii import unhexlify

from jasmine.parser_bases import NMEA0183FormatterBase
from jasmine.nmea2000 import PGN_DB, unpack_complete_message
from jasmine.exceptions import PGNError


class PCDINFormatter(NMEA0183FormatterBase):
    def sentence_formatter(self) -> str:
        return "DIN"

    def unpack(self, msg: List[str]) -> dict:
        """Unpack a wrapped --DIN message as received in a NMEA0183 stream

        Decodes --DIN sentences according to
        http://www.seasmart.net/pdf/SeaSmart_HTTP_Protocol_RevG_043012.pdf

        Args:
            msg (list): A list of strings containing the --DIN message

        Raises:
            PGNError:
                If we dont know how to decode as message associated with this PGN number

        Returns:
            dict: A fully unpacked --DIN message as a dict
        """
        # Unpack pgn
        pgn = int(msg[0], 16)

        if pgn not in PGN_DB or not PGN_DB[pgn]["Complete"]:
            raise PGNError(f"Cant decode message with PGN {pgn}", msg)

        # Unpack attributes
        timestamp = int(msg[1], 16)
        source_id = int(msg[2], 16)

        # Unpack message
        output = unpack_complete_message(pgn, unhexlify(msg[3]))

        # Add some attributes to output
        output["Timestamp"] = timestamp
        output["SourceID"] = source_id
        output["PGN"] = pgn

        return output