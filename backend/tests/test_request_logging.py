"""Tests for privacy-safe HTTP request logging."""

import logging

from fastapi.testclient import TestClient

from app.main import app


def test_request_logging_adds_and_reuses_request_id(caplog: object) -> None:
    """Every response carries a traceable request ID without exposing the body."""
    caplog.set_level(logging.INFO, logger="decisionlens.http")  # type: ignore[attr-defined]
    response = TestClient(app).get("/health", headers={"X-Request-ID": "test-request"})

    assert response.headers["X-Request-ID"] == "test-request"
    assert "request_completed request_id=test-request method=GET path=/health status=200" in caplog.text  # type: ignore[attr-defined]
