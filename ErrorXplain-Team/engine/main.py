"""
ErrorXplain backend - production entry point.

Exposes:
    GET  /health   - liveness probe + basic diagnostics (rule count,
                     whether AI fallback is configured)
    GET  /rules    - lists loaded rule IDs for a language (debugging aid)
    POST /explain  - parses a compiler error, tries offline rules, and
                     optionally falls back to AI

Startup/shutdown work (loading rules, opening/closing the shared AI
HTTP client) is managed via a FastAPI lifespan context manager rather
than the deprecated @app.on_event() hooks.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import rules_loader
from ai.ai_fallback import (
    close_ai_client,
    get_ai_explanation,
    init_ai_client,
    is_ai_configured,
)
from config import settings
from logging_config import configure_logging
from matcher.rule_matcher import match_rule
from models.schemas import ExplainRequest, ExplainResponse, Severity
from parser.error_parser import parse_error

configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Runs once at startup (before the first request) and once at shutdown."""
    logger.info("ErrorXplain engine starting...")

    rules_loader.load_all_rules()
    logger.info("Loaded %d rule(s) in total", rules_loader.get_rule_count())

    if is_ai_configured():
        logger.info("AI fallback: ENABLED")
    else:
        logger.info("AI fallback: DISABLED (no GROQ_API_KEY)")

    await init_ai_client()
    logger.info("Listening on http://%s:%d", settings.HOST, settings.PORT)

    yield

    logger.info("ErrorXplain engine shutting down...")
    await close_ai_client()


app = FastAPI(
    title=settings.APP_NAME,
    description="Offline-first engine that explains compiler/runtime errors in plain English.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    summary="Health check",
    description="Reports server liveness, how many offline rules are loaded, and whether AI fallback is configured.",
)
def health_check() -> Dict[str, object]:
    """Liveness probe with a couple of useful diagnostics."""
    return {
        "status": "ok",
        "rules_loaded": rules_loader.get_rule_count(),
        "ai_configured": is_ai_configured(),
    }


@app.get(
    "/rules",
    summary="List loaded rule IDs",
    description="Debugging aid for Person B: lists the rule IDs currently loaded for a language.",
)
def list_rules(language: str = "c") -> Dict[str, object]:
    """Return the loaded rule IDs for a language."""
    return {"language": language, "rule_ids": rules_loader.get_rule_ids(language)}


# Languages that have offline rules loaded via rules_loader.
_SUPPORTED_LANGUAGES = frozenset({"c", "python", "java"})


def _resolve_language(requested: str) -> str:
    """
    Map the requested language to the language used for rule lookup.

    "auto" resolves to "c". Supported languages: c, python, java.
    """
    if requested == "auto":
        return "c"
    if requested in _SUPPORTED_LANGUAGES:
        return requested
    raise HTTPException(
        status_code=400,
        detail=(
            f"Language '{requested}' is not supported yet. "
            f"Supported: {', '.join(sorted(_SUPPORTED_LANGUAGES))}."
        ),
    )


@app.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Explain a compiler/runtime error",
    description=(
        "Parses a raw compiler error, tries to match it against offline "
        "rules, and - only if nothing matches and allow_ai is true - "
        "falls back to an AI-generated, beginner-friendly explanation. "
        "ErrorXplain is offline-first, so AI is a bonus: if the AI "
        "service is unavailable, this still returns HTTP 200 with a "
        "safe fallback explanation rather than an error status."
    ),
)
async def explain_error(request: ExplainRequest) -> ExplainResponse:
    """
    Main endpoint.

    Flow: resolve language -> parse error -> try offline rules ->
    matched? return offline result : not allowed to use AI? return
    "no match" : call AI fallback and return its result (get_ai_explanation
    never raises for an AI-availability failure - it returns a safe
    fallback dict instead - so this always ends in an HTTP 200).
    """
    language = _resolve_language(request.language)
    logger.info("Received /explain request (language=%s, allow_ai=%s)", language, request.allow_ai)

    try:
        parsed = parse_error(request)
        rules = rules_loader.get_rules(language)
        matched_rule = match_rule(parsed, rules)

        if matched_rule is not None:
            logger.info("Offline rule matched: %s", matched_rule.id)
            return ExplainResponse(
                matched=True,
                language=language,
                category=matched_rule.category,
                severity=matched_rule.severity,
                explanation=matched_rule.explanation,
                suggestion=matched_rule.suggestion,
                source="offline",
                rule_id=matched_rule.id,
                file=parsed.file,
                line=parsed.line,
            )

        if not request.allow_ai:
            logger.info("No offline rule matched and allow_ai is False - returning 'no match'.")
            return ExplainResponse(
                matched=False,
                language=language,
                category="Unknown",
                severity=Severity.MEDIUM,
                explanation="No offline explanation found for this error.",
                suggestion="You can try using AI explanation if you want.",
                source="none",
                rule_id=None,
                file=parsed.file,
                line=parsed.line,
            )

        logger.warning("No offline rule matched - falling back to AI.")
        ai_result = await get_ai_explanation(
            error_message=request.error_message,
            language=language,
            source_code=request.source_code,
        )

        return ExplainResponse(
            matched=True,
            language=language,
            category="Unknown",
            severity=Severity.MEDIUM,
            explanation=ai_result["explanation"],
            suggestion=ai_result["suggestion"],
            source="ai",
            rule_id=None,
            file=parsed.file,
            line=parsed.line,
        )

    except HTTPException:
        raise  # already a well-formed client error - let it pass through unchanged
    except Exception:
        # Never leak internal tracebacks to the client.
        logger.exception("Unexpected error while handling /explain request.")
        raise HTTPException(status_code=500, detail="Internal server error.")
