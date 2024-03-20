import pytest


from sap_rfc_via_mqtt.serializer import Error, RfcError, RfcResult, serialize


def test_error_response():
    assert serialize(Error(error="Malformed RFC request")) == b'{"error":"Malformed RFC request"}'


def test_result_response():
    assert serialize(RfcResult(result={'myKey': 'my-value'})) == b'{"result":{"myKey":"my-value"}}'


def test_rfc_error_response():
    assert serialize(RfcError(rfcError="error-description", code=123)) == b'{"rfcError":"error-description","code":123}'


def test_arbitrary_response_type_is_not_allowed():
    with pytest.raises(TypeError):
        serialize('arbitrary-response')
