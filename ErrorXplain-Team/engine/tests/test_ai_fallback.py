"""
Unit tests for ai/ai_fallback.py.

The contract under test: get_ai_explanation() NEVER raises for an
AI-availability failure - every failure mode (no API key, timeout,
HTTP error status, network error, malformed response, missing fields)
must return SAFE_FALLBACK instead. This is what lets main.py always
respond with HTTP 200 (see tests/test_api.py for the endpoint-level
version of the same guarantee).

These tests talk to the real get_ai_explanation() function - nothing
here is mocked at the main.py level - so they exercise ai_fallback.py's
own error handling directly, not just main.py's wiring of whatever
get_ai_explanation() happens to return.

No real network calls are made: ai_fallback._client is monkeypatched
with a fake client that returns/raises exactly what we want, exactly
like the real httpx.AsyncClient would in each failure scenario.
"""

import asyncio

import httpx
import pytest

import ai.ai_fallback as ai_fallback
from ai.ai_fallback import SAFE_FALLBACK, get_ai_explanation


class _FakeResponse:
    """Stands in for httpx.Response - only the bits get_ai_explanation touches."""

    def __init__(self, json_data=None, status_error: Exception = None):
        self._json_data = json_data
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error is not None:
            raise self._status_error

    def json(self):
        return self._json_data


class _FakeClient:
    """Stands in for the shared httpx.AsyncClient."""

    def __init__(self, response: _FakeResponse = None, raise_on_post: Exception = None):
        self._response = response
        self._raise_on_post = raise_on_post
        self.post_call_count = 0

    async def post(self, url, json=None, headers=None):
        self.post_call_count += 1
        if self._raise_on_post is not None:
            raise self._raise_on_post
        return self._response


def _run(coro):
    """Run an async call without needing pytest-asyncio as a dev dependency."""
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _clean_ai_state(monkeypatch):
    """
    Every test gets AI enabled with a non-empty GROQ_API_KEY (unless it
    overrides them) and a cleared in-memory AI cache, so tests can't leak
    cached results or "not configured" state into each other.
    """
    monkeypatch.setattr(ai_fallback.settings, "AI_ENABLED", True)
    monkeypatch.setattr(ai_fallback.settings, "GROQ_API_KEY", "test-key")
    ai_fallback._ai_cache.clear()
    yield
    ai_fallback._ai_cache.clear()


def test_not_configured_returns_safe_fallback(monkeypatch):
    monkeypatch.setattr(ai_fallback.settings, "GROQ_API_KEY", "")
    fake_client = _FakeClient()
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error"))

    assert result == SAFE_FALLBACK
    # Not configured is checked before any network call is attempted.
    assert fake_client.post_call_count == 0


def test_ai_disabled_returns_safe_fallback(monkeypatch):
    monkeypatch.setattr(ai_fallback.settings, "AI_ENABLED", False)
    fake_client = _FakeClient()
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error"))

    assert result == SAFE_FALLBACK
    assert fake_client.post_call_count == 0


def test_timeout_returns_safe_fallback(monkeypatch):
    fake_client = _FakeClient(raise_on_post=httpx.TimeoutException("timed out"))
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error"))

    assert result == SAFE_FALLBACK


def test_http_status_error_returns_safe_fallback(monkeypatch):
    status_error = httpx.HTTPStatusError(
        "server error",
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        response=httpx.Response(500, request=httpx.Request("POST", "https://x")),
    )
    fake_response = _FakeResponse(status_error=status_error)
    fake_client = _FakeClient(response=fake_response)
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error"))

    assert result == SAFE_FALLBACK


def test_network_error_returns_safe_fallback(monkeypatch):
    fake_client = _FakeClient(raise_on_post=httpx.ConnectError("connection refused"))
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error"))

    assert result == SAFE_FALLBACK


def test_malformed_json_returns_safe_fallback(monkeypatch):
    # Groq answered, but the content isn't valid JSON at all.
    fake_response = _FakeResponse(
        json_data={"choices": [{"message": {"content": "not json"}}]}
    )
    fake_client = _FakeClient(response=fake_response)
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error"))

    assert result == SAFE_FALLBACK


def test_unexpected_shape_returns_safe_fallback(monkeypatch):
    # Groq answered 200 but the body doesn't have the expected structure.
    fake_response = _FakeResponse(json_data={"unexpected": "shape"})
    fake_client = _FakeClient(response=fake_response)
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error"))

    assert result == SAFE_FALLBACK


def test_missing_fields_returns_safe_fallback(monkeypatch):
    # Valid JSON content, but missing the explanation/suggestion keys we need.
    fake_response = _FakeResponse(
        json_data={
            "choices": [{"message": {"content": '{"explanation": "", "suggestion": ""}'}}]
        }
    )
    fake_client = _FakeClient(response=fake_response)
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error"))

    assert result == SAFE_FALLBACK


def test_successful_call_returns_result_and_caches(monkeypatch):
    fake_response = _FakeResponse(
        json_data={
            "choices": [
                {
                    "message": {
                        "content": '{"explanation": "Real explanation.", "suggestion": "Real suggestion."}'
                    }
                }
            ]
        }
    )
    fake_client = _FakeClient(response=fake_response)
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    result = _run(get_ai_explanation("main.c:1:1: error: some new error", language="c"))
    assert result == {"explanation": "Real explanation.", "suggestion": "Real suggestion."}
    assert fake_client.post_call_count == 1

    # Second identical call should be served from cache, not hit the client again.
    result2 = _run(get_ai_explanation("main.c:1:1: error: some new error", language="c"))
    assert result2 == result
    assert fake_client.post_call_count == 1


def test_fallback_results_are_not_cached(monkeypatch):
    fake_client = _FakeClient(raise_on_post=httpx.TimeoutException("timed out"))
    monkeypatch.setattr(ai_fallback, "_client", fake_client)

    _run(get_ai_explanation("main.c:1:1: error: some new error", language="c"))
    _run(get_ai_explanation("main.c:1:1: error: some new error", language="c"))

    # Both calls should have gone through to the (failing) client - a
    # fallback must never be cached, or a later real outage recovery
    # would be masked forever.
    assert fake_client.post_call_count == 2
