import os

from pyrfc import Connection, RFCError

from .messaging import MessageProcessor
from .parser import parse, ParseError
from .serializer import Error, RfcError, RfcResult, serialize

SAP_USER = os.environ['MS_SAP_USER']
SAP_PASSWORD = os.environ['MS_SAP_PASSWORD']
SAP_HOST = os.environ['MS_SAP_HOST']


class Facade(MessageProcessor):
    def __init__(self):
        self.connection = Connection(
            user=SAP_USER,
            passwd=SAP_PASSWORD,
            ashost=SAP_HOST,
        )

    def process(self, request: bytes) -> bytes:
        try:
            rfc = parse(request)
        except ParseError:
            return serialize(Error(error="Malformed RFC request"))

        try:
            result = self.connection.call(
                rfc.function, {}, **{param.name: param.value for param in rfc.parameters}
            )
        except RFCError:
            return serialize(RfcError(rfcError="RFC error"))

        return serialize(RfcResult(result=result))

    def close(self):
        self.connection.close()
