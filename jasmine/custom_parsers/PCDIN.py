from typing import List
from binascii import unhexlify

from jasmine.parser_bases import NMEA0183ProprietaryFormatterBase
from jasmine.nmea2000 import PGN_DB, unpack_complete_message
from jasmine.exceptions import PGNError


class PCDINFormatter(NMEA0183ProprietaryFormatterBase):
    def manufacturer_code(self) -> str:
        return "CDI"

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
        assert msg[0] == "N"
        # Unpack pgn
        pgn = int(msg[1], 16)

        if pgn not in PGN_DB or not PGN_DB[pgn]["Complete"]:
            raise PGNError(f"Cant decode message with PGN {pgn}", msg)

        # Unpack attributes
        timestamp = int(msg[2], 16)
        source_id = int(msg[3], 16)

        # Unpack message
        output = unpack_complete_message(pgn, unhexlify(msg[4]))

        # Add some attributes to output
        output["Timestamp"] = timestamp
        output["SourceID"] = source_id
        output["PGN"] = pgn

        return output