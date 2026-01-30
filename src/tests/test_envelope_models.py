# src/tests/test_envelope_models.py
import pytest
from pydantic import ValidationError

from schemas.common import Envelope, ErrorItem, ok


def test_ok_builder_creates_valid_envelope():
    env = ok(
        data={"status": "ok"},
        request_id="rid-123",
        self_url="/health",
    )
    assert env.data == {"status": "ok"}
    assert env.meta.request_id == "rid-123"
    assert env.links.self == "/health"
    assert env.errors == []


def test_envelope_forbids_extra_fields():
    with pytest.raises(ValidationError):
        Envelope(
            data={"x": 1},
            meta={"request_id": "rid-123"},
            links={"self": "/x"},
            errors=[],
            unexpected="nope",  # type: ignore
        )


def test_error_item_requires_code_and_message():
    with pytest.raises(ValidationError):
        ErrorItem(code="X") 