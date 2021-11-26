# pylint: disable=invalid-name
"""A parser for MXPGN messages
"""

from binascii import unhexlify
from typing import List

import bitstruct

from marulc.parser_bases import NMEA0183StandardFormatterBase
from marulc.nmea2000 import (
    PGN_DB,
    unpack_complete_message,
    process_sub_packet,
    packet_type,
)
from marulc.exceptions import PGNError


class MXPGNFormatter(NMEA0183StandardFormatterBase):
    """A parser for MXPGN messages, can handle both little-endian
    and big-endian byte-order"""

    def __init__(self, reverse_byte_ordering=False) -> None:
        super().__init__()
        self._reverse_byte_ordering = reverse_byte_ordering
        self._bucket = {}

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

        data = unhexlify(msg[2])
        if self._reverse_byte_ordering:
            data = data[::-1]

        # Unpack message
        if packet_type(pgn) == "Single":
            output = unpack_complete_message(pgn, data)
        elif packet_type(pgn) == "Fast":
            # Will raise if packet is not complete!
            complete_packet = process_sub_packet(
                pgn, source_address, data, self._bucket
            )
            output = unpack_complete_message(pgn, complete_packet)

        else:
            raise PGNError(f"Cant decode message with PGN {pgn}", msg)

        # Add some attributes to output
        output["Priority"] = priority
        output["SourceAddress"] = source_address
        output["PGN"] = pgn

        return output
