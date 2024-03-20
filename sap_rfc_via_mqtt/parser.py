import logging

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)
logger.propagate = False


class Rfc(BaseModel):
    class Parameter(BaseModel):
        name: str
        value: float | str

    function: str
    parameters: list[Parameter]


class ParseError(Exception):
    pass


def parse(message: bytes) -> Rfc:
    try:
        return Rfc.model_validate_json(message)
    except ValidationError as exc:
        logger.error('Malformed RFC request; reason=%s', exc)
        raise ParseError
