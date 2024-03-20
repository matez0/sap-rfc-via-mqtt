from unittest.mock import MagicMock, patch

import pytest
from pyrfc import RFCError

from sap_rfc_via_mqtt.facade import Facade
from sap_rfc_via_mqtt.parser import parse, ParseError, Rfc
from sap_rfc_via_mqtt.serializer import Error, RfcError, RfcResult, serialize


@pytest.fixture
def parser():
    return MagicMock(spec_set=parse)


@pytest.fixture
def serializer():
    return MagicMock(spec_set=serialize)


@pytest.fixture
def rfc_connection():
    return MagicMock()


@pytest.fixture
def facade(parser, serializer, rfc_connection):
    with \
            patch('sap_rfc_via_mqtt.facade.parse', new=parser), \
            patch('sap_rfc_via_mqtt.facade.Connection', return_value=rfc_connection), \
            patch('sap_rfc_via_mqtt.facade.serialize', new=serializer):
        yield Facade()


def test_connection_on_init():
    with patch('sap_rfc_via_mqtt.facade.Connection') as connection:
        Facade()
        connection.assert_called_once()


def test_close_connection_on_close(rfc_connection, facade):
    facade.close()

    rfc_connection.close.assert_called_once()


def test_process_rfc_and_return_result(parser, serializer, rfc_connection, facade):
    request = 'my-request'
    rfc = Rfc(
        function='my_func',
        parameters=[{'name': 'my_num', 'value': 123}, {'name': 'my_str', 'value': 'my-value'}]
    )
    parser.return_value = rfc
    rfc_connection.call.return_value = {'my_key': 'my-value'}

    assert facade.process(request) == serializer.return_value
    parser.assert_called_once_with(request)
    rfc_connection.call.assert_called_once_with(
        rfc.function, {}, **{param.name: param.value for param in rfc.parameters}
    )
    serializer.assert_called_once_with(RfcResult(result=rfc_connection.call.return_value))


def test_rfc_error(parser, serializer, rfc_connection, facade):
    request = 'my-request'
    rfc = Rfc(
        function='my_func',
        parameters=[{'name': 'my_num', 'value': 123}, {'name': 'my_str', 'value': 'my-value'}]
    )
    parser.return_value = rfc
    rfc_connection.call.side_effect = RFCError()

    assert facade.process(request) == serializer.return_value
    parser.assert_called_once_with(request)
    rfc_connection.call.assert_called_once_with(
        rfc.function, {}, **{param.name: param.value for param in rfc.parameters}
    )
    serializer.assert_called_once_with(RfcError(rfcError="RFC error"))


def test_parse_error(parser, serializer, rfc_connection, facade):
    request = 'my-request'
    parser.side_effect = ParseError()

    assert facade.process(request) == serializer.return_value
    parser.assert_called_once_with(request)
    serializer.assert_called_once_with(Error(error="Malformed RFC request"))
    rfc_connection.call.assert_not_called()
