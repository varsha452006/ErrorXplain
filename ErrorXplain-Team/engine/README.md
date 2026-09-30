# ErrorXplain Engine

Offline-first backend that explains C compiler errors in plain English,
with an optional AI fallback (Groq/Llama) for errors no offline rule
recognizes yet.

## What it does

1. Receives a raw compiler error (and optionally the source code).
2. Parses it to find the file, line, and the actual error text (gcc/
   clang multi-line output is handled - notes are ignored, and an
   `error:` line always wins over a `warning:` line).
3. Tries to match the error against offline rules loaded from
   `rules/c/rules.json`.
4. If a rule matches -> returns that rule's explanation (`source: "offline"`).
5. If nothing matches and `allow_ai` is `false` -> returns a
   "no explanation found" response (`source: "none"`).
6. If nothing matches and `allow_ai` is `true` -> asks Groq's Llama
   model for a beginner-friendly explanation (`source: "ai"`). If the
   AI service can't be reached, this still returns HTTP 200 with a
   safe, honest fallback explanation - ErrorXplain is offline-first,
   so AI is a bonus, never a hard dependency the caller has to handle
   errors for.

Only C is implemented right now; C++ and Python are reserved in the
API but not yet supported.

## Project structure

```
engine/
├── main.py                 # FastAPI app: /health, /rules, POST /explain
├── config.py                # All settings, read from environment/.env
├── logging_config.py        # Root logger setup
├── conftest.py               # Makes engine/ importable for pytest
├── parser/
│   └── error_parser.py      # Parses raw gcc/clang error text
├── matcher/
│   └── rule_matcher.py      # Matches parsed errors against loaded rules
├── ai/
│   └── ai_fallback.py       # Groq AI fallback: client, cache, sanitization
├── models/
│   └── schemas.py           # Pydantic request/response models + enums
├── rules_loader.py          # Loads + caches rules/<language>/rules.json
├── tests/
│   ├── test_parser.py
│   ├── test_matcher.py
│   └── test_api.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── README.md

rules/
└── c/
    └── rules.json           # Person B edits this file only
```

## Install and run

```bash
cd engine
pip install -r requirements.txt
cp .env.example .env
# edit .env and set GROQ_API_KEY if you want AI fallback to work

uvicorn main:app --reload
```

The API is live at `http://127.0.0.1:8000`, with interactive docs at
`http://127.0.0.1:8000/docs`.

## Environment variables

See `.env.example` for the full list with defaults. The only one you
must set yourself to get AI fallback working is `GROQ_API_KEY` - every
other variable has a sensible default (server host/port, CORS origins,
rule directory, request-size limits, Groq model/timeout/cache settings).

If `GROQ_API_KEY` is not set, `allow_ai: true` requests still return
HTTP 200, with the safe fallback explanation/suggestion in place of a
real AI answer - never a 503, and never a crash.

## Endpoints

### `GET /health`
```json
{ "status": "ok", "rules_loaded": 5, "ai_configured": false }
```

### `GET /rules?language=c`
Lists loaded rule IDs - useful for confirming Person B's `rules.json`
loaded correctly without exposing the full rule content.

### `POST /explain`

**Case 1 - offline rule matched:**
```bash
curl -X POST http://127.0.0.1:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "main.c:5:9: error: expected '"'"';'"'"' before '"'"'return'"'"'",
    "language": "c",
    "allow_ai": false
  }'
```
```json
{
  "matched": true, "language": "c", "category": "Syntax", "severity": "Medium",
  "explanation": "You are missing a semicolon (;) at the end of a statement.",
  "suggestion": "Add a semicolon at the end of the previous line.",
  "source": "offline", "rule_id": "c_missing_semicolon", "file": "main.c", "line": 5
}
```

**Case 2 - no match, AI not allowed:**
```bash
curl -X POST http://127.0.0.1:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"error_message": "main.c:1:1: error: some brand new error", "language": "c", "allow_ai": false}'
```
Returns `"matched": false, "source": "none"`.

**Case 3 - no match, AI allowed (AI available):**
```bash
curl -X POST http://127.0.0.1:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"error_message": "main.c:1:1: error: some brand new error", "language": "c", "allow_ai": true}'
```
Returns `"matched": true, "source": "ai"` with a beginner-friendly
explanation and suggestion.

**Case 4 - no match, AI allowed but AI service unavailable:**
Same request as Case 3, but if Groq can't be reached (no API key,
network error, timeout, or a Groq server error), the response is
still HTTP 200, with a safe, honest fallback in place of a real answer:
```json
{
  "matched": true, "language": "c", "category": "Unknown", "severity": "Medium",
  "explanation": "We could not get an AI explanation for this error right now.",
  "suggestion": "Please check your code carefully near the reported line, or try again in a moment.",
  "source": "ai", "rule_id": null, "file": "main.c", "line": 1
}
```

PowerShell equivalent for any of the above:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/explain" -Method Post `
  -ContentType "application/json" `
  -Body '{"error_message": "main.c:5:9: error: expected '\'';'\'' before '\''return'\''", "language": "c", "allow_ai": false}'
```

## Adding rules (Person B)

Edit `rules/c/rules.json`. Each rule looks like:

```json
{
  "id": "c_missing_semicolon",
  "language": "c",
  "patterns": ["expected ';' before"],
  "category": "Syntax",
  "severity": "Medium",
  "explanation": "...",
  "suggestion": "...",
  "tags": ["syntax", "semicolon"]
}
```

`patterns` are matched case-insensitively, as both a plain substring
and a regex - most of the time plain text is all you need. Rules are
loaded once at startup, so **restart the server** after editing
`rules.json` for changes to take effect.

## Running tests

```bash
cd engine
pip install -r requirements-dev.txt
pytest -v
```

Tests never call the real Groq API - the AI call is mocked in
`tests/test_api.py`.

## Notes on production hardening

- Rules are loaded once at startup and cached in memory (see
  `rules_loader.py`); a missing or corrupt `rules.json` is logged as a
  WARNING and treated as zero rules, not a crash.
- The AI fallback reuses a single `httpx.AsyncClient` for the app's
  lifetime, sanitizes error text/source code before sending it to
  Groq, and caches identical `(language, error_message)` results for
  `AI_CACHE_TTL_SECONDS` (default 5 minutes).
- CORS is restricted to `CORS_ORIGINS` (default: localhost only) -
  update this for your real frontend's origin before deploying.
- No raw exception tracebacks are ever returned to the client; the
  full traceback is only ever written to the server log.
