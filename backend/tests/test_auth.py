"""Tests for the basic-auth middleware.

Uses TestClient against a fresh app instance built with auth env vars set,
since main.py reads APP_USERNAME/APP_PASSWORD (and therefore AUTH_ENABLED)
once at import time.
"""
import base64
import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _fresh_app(monkeypatch, username=None, password=None):
    """Reimport auth + main with the given env vars, so AUTH_ENABLED is
    recomputed for this test rather than reusing a cached module."""
    if username is not None:
        monkeypatch.setenv("APP_USERNAME", username)
    else:
        monkeypatch.delenv("APP_USERNAME", raising=False)
    if password is not None:
        monkeypatch.setenv("APP_PASSWORD", password)
    else:
        monkeypatch.delenv("APP_PASSWORD", raising=False)

    for mod in ("auth", "main"):
        sys.modules.pop(mod, None)
    import main as main_module
    return main_module.app


def _basic_header(user: str, pwd: str) -> dict:
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_auth_disabled_when_env_vars_unset(monkeypatch):
    from fastapi.testclient import TestClient
    app = _fresh_app(monkeypatch, username=None, password=None)
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_auth_blocks_without_credentials(monkeypatch):
    from fastapi.testclient import TestClient
    app = _fresh_app(monkeypatch, username="labuser", password="s3cret")
    client = TestClient(app)
    resp = client.get("/api/health")
    # health stays open even with auth enabled
    assert resp.status_code == 200
    resp = client.post("/api/predict", json={"fasta": ">t\nAAAA\n"})
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate", "").lower().startswith("basic")


def test_auth_rejects_wrong_credentials(monkeypatch):
    from fastapi.testclient import TestClient
    app = _fresh_app(monkeypatch, username="labuser", password="s3cret")
    client = TestClient(app)
    resp = client.post(
        "/api/predict",
        json={"fasta": ">t\nAAAA\n"},
        headers=_basic_header("wrong", "creds"),
    )
    assert resp.status_code == 401


def test_auth_accepts_correct_credentials(monkeypatch):
    from fastapi.testclient import TestClient
    app = _fresh_app(monkeypatch, username="labuser", password="s3cret")
    client = TestClient(app)
    resp = client.post(
        "/api/predict",
        json={"fasta": ">tat\nGRKKRRQRRRPPQ\n"},
        headers=_basic_header("labuser", "s3cret"),
    )
    assert resp.status_code == 200
    assert resp.json()["predictions"][0]["predicted_class"] == "CPP"
