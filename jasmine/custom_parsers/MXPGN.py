from binascii import unhexlify
from typing import List

import bitstruct

from jasmine.parser_bases import NMEA0183StandardFormatterBase
from jasmine.nmea2000 import (
    PGN_DB,
    unpack_complete_message,
    process_sub_packet,
    packet_type,
)
from jasmine.exceptions import PGNError


class MXPGNFormatter(NMEA0183StandardFormatterBase):
    def __init__(self) -> None:
        super().__init__()
        self._bucket = dict()

    def sentence_formatter(self) -> str:
        return "PGN"

    def unpack(self, msg: List[str]) -> dict:
        """Unpack a wrapped --PGN message as received in a NMEA0183 stream

        Decodes --PGN sentences according to
        https://opencpn.org/wiki/dokuwiki/lib/exe/fetch.php?media=opencpn:software:mxpgn_sentence.pdf

        Args:
            msg (list): A list of strings containing the --PGN message

        Raises:
            PGNError:
                If we dont know how to decode as message associated with this PGN number
            MultiPacketDiscardedError:
                If this subpacket is discarded due to missing messages
            MultiPacketInProcessError:
                If this subpacket has been processed successfully but we require more
                subpackets to be able to decode the full message

        Returns:
            dict: A fully unpacked --PGN message as a dict
        """
        # Unpack pgn
        pgn = int(msg[0], 16)

        if pgn not in PGN_DB or not PGN_DB[pgn]["Complete"]:
            raise PGNError(f"Cant decode message with PGN {pgn}", msg)

        # Unpack attributes
        _, priority, _, source_address = bitstruct.unpack(
            ">u1u3u4u8", unhexlify(msg[1])
        )

        # Unpack message
        if packet_type(pgn) == "Single":
            output = unpack_complete_message(pgn, unhexlify(msg[2]))
        elif packet_type(pgn) == "Fast":
            # Will raise if packet is not complete!
            complete_packet = process_sub_packet(
                pgn, source_address, unhexlify(msg[2]), self._bucket
            )
            output = unpack_complete_message(pgn, complete_packet)

        else:
            raise PGNError(f"Cant decode message with PGN {pgn}", msg)

        # Add some attributes to output
        output["Priority"] = priority
        output["SourceAddress"] = source_address
        output["PGN"] = pgn

        return output