"""Focused checks for safe, structured operational logging."""

import json
import logging

from app.core.logging import StructuredFormatter


def test_structured_formatter_keeps_only_reviewed_operational_context() -> None:
    """Request logs retain a clear path while omitting arbitrary sensitive extras."""
    record = logging.LogRecord(
        name="citizen_intelligence",
        level=logging.INFO,
        pathname=__file__,
        lineno=20,
        msg="Request completed",
        args=(),
        exc_info=None,
    )
    record.event = "request_completed"
    record.path = "/health/ready"
    record.status_code = 200
    record.authorization = "must-not-be-logged"

    payload = json.loads(StructuredFormatter().format(record))

    assert payload["message"] == "Request completed"
    assert payload["context"] == {
        "event": "request_completed",
        "path": "/health/ready",
        "status_code": 200,
    }
    assert "authorization" not in payload
