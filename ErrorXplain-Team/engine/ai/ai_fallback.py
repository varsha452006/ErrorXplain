"""
AI fallback module.

Called ONLY when no offline rule matched an error AND the caller set
allow_ai = true. Uses Groq's OpenAI-compatible chat completions API to
generate a beginner-friendly explanation + suggestion.

This module owns three production concerns:
    - A single reusable httpx.AsyncClient (created at app startup,
      closed at shutdown - never created fresh per request).
    - A small in-memory cache so identical errors don't trigger a new
      AI call every time within a short window.
    - Sanitization of user-supplied text before it leaves our server.

ErrorXplain is offline-first: AI is a bonus, never a hard dependency.
So get_ai_explanation() NEVER raises for a failure to get an AI answer -
it always returns a dict with "explanation"/"suggestion" keys. Any
failure (AI disabled, no API key, network/timeout errors, Groq returning
a server error, or unparseable content) results in SAFE_FALLBACK, and
the caller (main.py) always returns HTTP 200 with it - never a 503.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Dict, Optional, Tuple

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Language-specific beginner-friendly system prompts.
_LANGUAGE_PROMPTS: Dict[str, str] = {
    "c": (
        "Explain this C programming error in very simple language that a "
        "complete beginner can understand. First tell what went wrong in "
        "plain English. Then clearly tell what the student should do to fix "
        "it. Do not use advanced technical terms."
    ),
    "python": (
        "Explain this Python error in very simple language that a complete "
        "beginner can understand. First tell what went wrong in plain English. "
        "Then clearly tell what the student should do to fix it. Do not use "
        "advanced technical terms."
    ),
    "java": (
        "Explain this Java error in very simple language that a complete "
        "beginner can understand. First tell what went wrong in plain English. "
        "Then clearly tell what the student should do to fix it. Do not use "
        "advanced technical terms."
    ),
    "cpp": (
        "Explain this C++ programming error in very simple language that a "
        "complete beginner can understand. First tell what went wrong in "
        "plain English. Then clearly tell what the student should do to fix "
        "it. Do not use advanced technical terms."
    ),
}

_DEFAULT_PROMPT = (
    "Explain this programming error in very simple language that a complete "
    "beginner can understand. First tell what went wrong in plain English. "
    "Then clearly tell what the student should do to fix it. Do not use "
    "advanced technical terms."
)

# Forces the model to answer in a shape we can drop straight into our schema.
RESPONSE_FORMAT_INSTRUCTIONS = (
    "Reply with ONLY a JSON object, no extra text, in exactly this shape: "
    '{"explanation": "...", "suggestion": "..."}. '
    '"explanation" should say what went wrong in 1-2 simple sentences. '
    '"suggestion" should say what the student should do to fix it, in '
    "1-2 simple sentences."
)

# Returned for ANY AI failure - not configured, network/timeout, server
# error, or soft failures (reachable but unusable content). Honest wording.
SAFE_FALLBACK: Dict[str, str] = {
    "explanation": "We could not get an AI explanation for this error right now.",
    "suggestion": "Please check your code carefully near the reported line, or try again in a moment.",
}

# Strips ASCII control characters (except normal whitespace) before we
# send anything to a third-party API.
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Shared HTTP client, created once at startup and reused for every request.
_client: Optional[httpx.AsyncClient] = None

# In-memory cache: (language, sanitized_error_message) -> (expires_at, result).
_ai_cache: Dict[Tuple[str, str], Tuple[float, Dict[str, str]]] = {}


def is_ai_configured() -> bool:
    """
    Whether AI fallback can be attempted.

    Requires both AI_ENABLED=true and a non-empty GROQ_API_KEY.
    Used by /health and by get_ai_explanation before any network call.
    """
    return bool(settings.AI_ENABLED) and bool(settings.GROQ_API_KEY)


async def init_ai_client() -> None:
    """Create the shared httpx.AsyncClient. Call once, at app startup."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS)
        logger.info(
            "AI HTTP client initialized (timeout=%.1fs, enabled=%s)",
            settings.AI_TIMEOUT_SECONDS,
            settings.AI_ENABLED,
        )


async def close_ai_client() -> None:
    """Close the shared httpx.AsyncClient. Call once, at app shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("AI HTTP client closed")


def _sanitize(text: str, max_length: int) -> str:
    """Strip control characters and cap length before sending text to the AI."""
    cleaned = _CONTROL_CHAR_PATTERN.sub("", text)
    return cleaned[:max_length].strip()


def _cache_get(key: Tuple[str, str]) -> Optional[Dict[str, str]]:
    """Return a cached AI result for this key if present and not expired."""
    entry = _ai_cache.get(key)
    if entry is None:
        return None
    expires_at, result = entry
    if time.monotonic() >= expires_at:
        _ai_cache.pop(key, None)
        return None
    return result


def _cache_set(key: Tuple[str, str], result: Dict[str, str]) -> None:
    """Store an AI result for AI_CACHE_TTL_SECONDS."""
    expires_at = time.monotonic() + settings.AI_CACHE_TTL_SECONDS
    _ai_cache[key] = (expires_at, result)


def _system_prompt_for(language: str) -> str:
    """Pick a language-specific system prompt, with a safe default."""
    return _LANGUAGE_PROMPTS.get(language.lower(), _DEFAULT_PROMPT)


def _error_label_for(language: str) -> str:
    """Human-readable label used in the user message."""
    labels = {
        "c": "C compiler error",
        "cpp": "C++ compiler error",
        "python": "Python error",
        "java": "Java error",
    }
    return labels.get(language.lower(), "programming error")


def _build_payload(
    sanitized_error: str,
    language: str,
    sanitized_source: Optional[str],
) -> Dict[str, object]:
    """Build the Groq chat-completions request body."""
    user_content = f"{_error_label_for(language)}:\n{sanitized_error}"
    if sanitized_source:
        user_content += f"\n\nRelevant source code:\n{sanitized_source}"
    user_content += f"\n\n{RESPONSE_FORMAT_INSTRUCTIONS}"

    return {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": _system_prompt_for(language)},
            {"role": "user", "content": user_content},
        ],
        "temperature": settings.AI_TEMPERATURE,
        "max_tokens": settings.AI_MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }


async def get_ai_explanation(
    error_message: str,
    language: str = "c",
    source_code: Optional[str] = None,
) -> Dict[str, str]:
    """
    Ask Groq to explain a compiler/runtime error in beginner-friendly terms.

    Returns a dict with "explanation" and "suggestion" keys - ALWAYS.
    This function never raises for an AI-availability failure: AI disabled,
    no API key, network/timeout error, server error, or unusable content
    all result in SAFE_FALLBACK so the caller can always respond HTTP 200.

    Identical (language, error_message) pairs are served from a short
    in-memory cache. Fallback results are never cached, so the next
    request tries the AI again instead of repeating a stale outage response.
    """
    if not is_ai_configured():
        logger.warning(
            "AI fallback requested but AI is not configured "
            "(AI_ENABLED=%s, key_present=%s) - using safe fallback.",
            settings.AI_ENABLED,
            bool(settings.GROQ_API_KEY),
        )
        return dict(SAFE_FALLBACK)

    sanitized_error = _sanitize(error_message, settings.MAX_ERROR_MESSAGE_LENGTH)
    sanitized_source = (
        _sanitize(source_code, settings.MAX_SOURCE_CODE_LENGTH) if source_code else None
    )

    cache_key = (language, sanitized_error)
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info(
            "AI cache hit (language=%s, error length=%d)", language, len(sanitized_error)
        )
        return cached

    payload = _build_payload(sanitized_error, language, sanitized_source)
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # Prefer the shared client; fall back to a temporary one only if
    # init_ai_client() was somehow never called (e.g. standalone script).
    client = _client
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS)

    try:
        try:
            response = await client.post(
                settings.GROQ_API_URL, json=payload, headers=headers
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("Groq request timed out - using safe fallback: %s", exc)
            return dict(SAFE_FALLBACK)
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Groq returned HTTP %s - using safe fallback.",
                exc.response.status_code,
            )
            return dict(SAFE_FALLBACK)
        except httpx.HTTPError as exc:
            logger.warning("Network error calling Groq - using safe fallback: %s", exc)
            return dict(SAFE_FALLBACK)

        try:
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_content)
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Groq response was malformed or not valid JSON: %s", exc)
            return dict(SAFE_FALLBACK)

        explanation = str(parsed.get("explanation", "")).strip()
        suggestion = str(parsed.get("suggestion", "")).strip()

        if not explanation or not suggestion:
            logger.warning(
                "Groq response was missing explanation/suggestion - using safe fallback."
            )
            return dict(SAFE_FALLBACK)

        result = {"explanation": explanation, "suggestion": suggestion}
        _cache_set(cache_key, result)
        logger.info("AI explanation generated successfully (language=%s)", language)
        return result

    finally:
        if owns_client:
            await client.aclose()
