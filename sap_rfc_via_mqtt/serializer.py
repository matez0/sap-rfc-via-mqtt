from functools import singledispatch

from pydantic import BaseModel


class Error(BaseModel):
    error: str


class RfcResult(BaseModel):
    result: dict


class RfcError(BaseModel):
    rfcError: str
    code: int | None = None


@singledispatch
def serialize(response):
    raise TypeError('Unknown response type')


@serialize.register
def _(response: RfcResult | RfcError | Error) -> bytes:
    return response.model_dump_json().encode()
