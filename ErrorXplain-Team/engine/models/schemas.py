"""
Pydantic models for ErrorXplain's public API.

These define the exact shape of the request and response for
POST /explain. Field constraints here are the first line of input
validation - FastAPI turns any violation into an HTTP 422 automatically,
before our own code ever runs.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Language(str, Enum):
    """
    Languages the API accepts.

    C, Python, and Java have offline rules. CPP is reserved for future
    use. AUTO resolves to "c" when the language cannot be inferred.
    """

    C = "c"
    CPP = "cpp"
    PYTHON = "python"
    JAVA = "java"
    AUTO = "auto"


class Severity(str, Enum):
    """How serious an error/warning is. Used by both rules and responses."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Source(str, Enum):
    """Where an explanation ultimately came from."""

    OFFLINE = "offline"
    AI = "ai"
    NONE = "none"


class ExplainRequest(BaseModel):
    """Incoming request body for POST /explain."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_message": "main.c:5:9: error: expected ';' before 'return'",
                "language": "c",
                "source_code": None,
                "allow_ai": False,
            }
        }
    )

    error_message: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="Full raw error text from the compiler/interpreter. Cannot be empty.",
    )
    language: Language = Field(
        default=Language.AUTO,
        description="Language the error came from: c, python, java, or auto (defaults to c).",
    )
    source_code: Optional[str] = Field(
        default=None,
        max_length=20000,
        description="Optional source code for extra context (used only by the AI fallback).",
    )
    allow_ai: bool = Field(
        default=False,
        description="Whether AI fallback is allowed when no offline rule matches.",
    )


class ExplainResponse(BaseModel):
    """Outgoing response body for POST /explain. Shape is always the same."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matched": True,
                "language": "c",
                "category": "Syntax",
                "severity": "Medium",
                "explanation": "You are missing a semicolon (;) at the end of a statement.",
                "suggestion": "Add a semicolon at the end of the previous line.",
                "source": "offline",
                "rule_id": "c_missing_semicolon",
                "file": "main.c",
                "line": 5,
            }
        }
    )

    matched: bool = Field(..., description="Whether an explanation was found (offline or AI).")
    language: str = Field(..., description="Language the error was interpreted as.")
    # Category stays a free-form string (not an enum) on purpose: Person B
    # can introduce new categories in rules.json without a code change.
    category: str = Field(..., description="Category of the error, e.g. Syntax, Reference, Runtime, Unknown.")
    severity: Severity = Field(..., description="How serious the error/warning is.")
    explanation: str = Field(..., description="Plain-English explanation of what went wrong.")
    suggestion: str = Field(..., description="What the user should do to fix it.")
    source: Source = Field(..., description="Where the explanation came from: offline, ai, or none.")
    rule_id: Optional[str] = Field(default=None, description="ID of the offline rule that matched, if any.")
    file: Optional[str] = Field(default=None, description="Source file extracted from the error, if any.")
    line: Optional[int] = Field(default=None, description="Line number extracted from the error, if any.")
