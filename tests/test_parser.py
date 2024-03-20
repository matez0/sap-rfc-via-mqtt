import pytest

from sap_rfc_via_mqtt.parser import parse, ParseError, Rfc


def test_parse_rfc_request_message():
    message = b'''{
    "function": "my_func",
    "parameters": [
        {"name": "my_num", "value": 12.3},
        {"name": "my_str", "value": "my_value"}
    ]
}'''

    result = parse(message)

    assert isinstance(result, Rfc)
    assert result.function == 'my_func'
    assert result.parameters[0].name == 'my_num'
    assert result.parameters[0].value == 12.3
    assert result.parameters[1].name == 'my_str'
    assert result.parameters[1].value == 'my_value'


def test_error_when_message_is_malformed():
    message = b'''{
    "parameters": []
}'''

    with pytest.raises(ParseError):
        parse(message)
