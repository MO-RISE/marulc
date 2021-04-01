"""
Exceptions
"""


class ParseError(ValueError):
    def __init__(self, message, data):
        super(ParseError, self).__init__((message, data))


class SentenceTypeError(ParseError):
    pass


class ChecksumError(ParseError):
    pass


class PGNError(ParseError):
    pass


class MultiPacketError(RuntimeError):
    pass


class MultiPacketInProcessError(MultiPacketError):
    pass


class MultiPacketDiscardedError(MultiPacketError):
    pass
