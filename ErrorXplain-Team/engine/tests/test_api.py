"""
End-to-end tests for POST /explain via FastAPI's TestClient.

Covers all key cases:
    1. Offline rule match (C, Python, Java)
    2. No match + allow_ai=False
    3. No match + allow_ai=True, AI succeeds (mocked)
    4. No match + allow_ai=True, AI fails -> still HTTP 200 with the
       safe fallback explanation (mocked). ErrorXplain is offline-first,
       so an AI outage is never surfaced as an error status to the
       caller - see ai/ai_fallback.py, which never raises for this.
    5. Empty error_message -> HTTP 422
    6. Unsupported language -> HTTP 400

The real Groq API is never called - main.get_ai_explanation is
monkeypatched for cases 3 and 4.
"""

import pytest
from fastapi.testclient import TestClient

import main
from ai.ai_fallback import SAFE_FALLBACK


@pytest.fixture
def client():
    # Using TestClient as a context manager triggers the lifespan
    # handler, so rules actually get loaded before each test runs.
    with TestClient(main.app) as test_client:
        yield test_client


def test_offline_match(client):
    response = client.post(
        "/explain",
        json={
            "error_message": "main.c:5:9: error: expected ';' before 'return'",
            "language": "c",
            "allow_ai": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["source"] == "offline"
    assert body["rule_id"] == "c_missing_semicolon"


def test_python_offline_match(client):
    response = client.post(
        "/explain",
        json={
            "error_message": "NameError: name 'user_id' is not defined",
            "language": "python",
            "allow_ai": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["source"] == "offline"
    assert body["language"] == "python"
    assert body["rule_id"] == "py_name_not_defined"


def test_java_offline_match(client):
    response = client.post(
        "/explain",
        json={
            "error_message": 'Exception in thread "main" java.lang.NullPointerException',
            "language": "java",
            "allow_ai": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["source"] == "offline"
    assert body["language"] == "java"
    assert body["rule_id"] == "java_null_pointer"


def test_no_match_without_ai(client):
    response = client.post(
        "/explain",
        json={
            "error_message": "main.c:1:1: error: some brand new error nobody has a rule for",
            "language": "c",
            "allow_ai": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is False
    assert body["source"] == "none"


def test_no_match_with_ai_success(client, monkeypatch):
    async def fake_ai(*args, **kwargs):
        return {"explanation": "Fake explanation.", "suggestion": "Fake suggestion."}

    monkeypatch.setattr("main.get_ai_explanation", fake_ai)

    response = client.post(
        "/explain",
        json={
            "error_message": "main.c:1:1: error: some brand new error nobody has a rule for",
            "language": "c",
            "allow_ai": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["source"] == "ai"
    assert body["explanation"] == "Fake explanation."


def test_no_match_with_ai_failure_returns_safe_fallback(client, monkeypatch):
    # get_ai_explanation itself never raises for an AI-availability
    # failure (see tests/test_ai_fallback.py) - it returns SAFE_FALLBACK.
    # This test simulates exactly that return value to confirm main.py
    # wires it through as a normal HTTP 200, not an error status.
    async def fake_ai_failure(*args, **kwargs):
        return dict(SAFE_FALLBACK)

    monkeypatch.setattr("main.get_ai_explanation", fake_ai_failure)

    response = client.post(
        "/explain",
        json={
            "error_message": "main.c:1:1: error: some brand new error nobody has a rule for",
            "language": "c",
            "allow_ai": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["source"] == "ai"
    assert body["explanation"] == SAFE_FALLBACK["explanation"]
    assert body["suggestion"] == SAFE_FALLBACK["suggestion"]


def test_empty_error_message_returns_422(client):
    response = client.post(
        "/explain",
        json={"error_message": "", "language": "c", "allow_ai": False},
    )
    assert response.status_code == 422


def test_unsupported_language_returns_400(client):
    response = client.post(
        "/explain",
        json={"error_message": "some error", "language": "cpp", "allow_ai": False},
    )
    assert response.status_code == 400


def test_health_endpoint_reports_diagnostics(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rules_loaded"] >= 1
    assert "ai_configured" in body