"""Tests for the /api/contact endpoint. Doesn't test actual Resend delivery
(no real API key in CI) — tests validation and the unconfigured-API-key
error path, which is what's actually testable without live credentials."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_contact_requires_all_fields():
    resp = client.post("/api/contact", json={
        "name": "", "email": "test@example.com", "subject": "", "comment": "",
    })
    assert resp.status_code == 400


def test_contact_rejects_invalid_email():
    resp = client.post("/api/contact", json={
        "name": "Test", "email": "not-an-email", "subject": "Hi", "comment": "hello",
    })
    assert resp.status_code == 422


def test_contact_rejects_overlong_message():
    resp = client.post("/api/contact", json={
        "name": "Test", "email": "test@example.com", "subject": "Hi",
        "comment": "x" * 5001,
    })
    assert resp.status_code == 400


def test_contact_fails_loudly_when_resend_unconfigured(monkeypatch):
    # RESEND_CONFIGURED is computed at import time, so reimport with the
    # env var cleared (same pattern as test_auth.py's _fresh_app helper).
    # Also clear auth env vars and pop the auth module — otherwise this
    # test can inherit AUTH_ENABLED=True left cached by test_auth.py's
    # tests running earlier in the same session, and get a 401 instead.
    for var in ("RESEND_API_KEY", "APP_USERNAME", "APP_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    for mod in ("mailer", "auth", "main"):
        sys.modules.pop(mod, None)
    import main as fresh_main
    fresh_client = TestClient(fresh_main.app)

    resp = fresh_client.post("/api/contact", json={
        "name": "Test", "email": "test@example.com", "subject": "Hi",
        "comment": "hello there",
    })
    assert resp.status_code == 503
    assert "RESEND_API_KEY" in resp.json()["detail"]
