"""
Error parser for C compiler messages (gcc / clang style).

This module's only job is to pull structural info (file, line, level,
main message) out of a raw compiler error string. It does NOT decide
what the error means - that is the rule matcher's job.

Real gcc/clang output is usually MULTIPLE lines, e.g.:

    main.c: In function 'main':
    main.c:5:9: error: expected ';' before 'return'
        5 |     return 0;
          |         ^
    main.c:5:9: note: each undeclared identifier is reported only once

We only care about diagnostic lines shaped like:
    <file>:<line>:<column>: <error|warning|note>: <message>

Everything else (context lines like "In function 'main':", source
snippets, caret lines "^") is ignored automatically - it simply won't
match the pattern below.
"""

import logging
import re
from typing import List, Optional

from models.schemas import ExplainRequest, Language

logger = logging.getLogger(__name__)


class ParsedError:
    """Structured result of parsing a raw compiler error message."""

    def __init__(
        self,
        raw_message: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        level: Optional[str] = None,  # "error" | "warning" | "note"
    ) -> None:
        self.raw_message = raw_message
        self.file = file
        self.line = line
        self.column = column
        self.level = level


# Matches: <file>:<line>:<column>: <error|warning|note>: <message>
# Example: main.c:5:9: error: expected ';' before 'return'
DIAGNOSTIC_PATTERN = re.compile(
    r"^(?P<file>[^\s:][^:]*):(?P<line>\d+):(?P<column>\d+):\s*"
    r"(?P<level>error|warning|note):\s*(?P<message>.+)$"
)


class _Diagnostic:
    """One parsed diagnostic line, before we decide which one 'wins'."""

    def __init__(self, file: str, line: int, column: int, level: str, message: str) -> None:
        self.file = file
        self.line = line
        self.column = column
        self.level = level
        self.message = message


def _extract_diagnostics(error_message: str) -> List[_Diagnostic]:
    """
    Scan every line of the raw compiler output and pull out every line
    that matches the <file>:<line>:<col>: <level>: <message> shape.

    Source snippets, caret ("^") lines, and "In function 'x':" context
    lines are skipped automatically since they don't match the pattern.
    """
    diagnostics: List[_Diagnostic] = []

    for raw_line in error_message.splitlines():
        match = DIAGNOSTIC_PATTERN.match(raw_line.strip())
        if not match:
            continue

        diagnostics.append(
            _Diagnostic(
                file=match.group("file"),
                line=int(match.group("line")),
                column=int(match.group("column")),
                level=match.group("level"),
                message=match.group("message").strip(),
            )
        )

    return diagnostics


def parse_c_error(error_message: str) -> ParsedError:
    """
    Parse a raw C compiler error message (gcc/clang format), which may
    span multiple lines.

    Selection rule for which diagnostic line becomes the "main" error:
        1. Ignore all "note:" lines entirely - they only add context
           and are never the main problem.
        2. If any "error:" line exists, use the FIRST one. Errors
           always outrank warnings.
        3. Otherwise, if only "warning:" lines exist, use the first one.
        4. If nothing matches the gcc/clang shape at all, fall back to
           passing the raw text through untouched so the rule matcher
           still has something to work with.
    """
    diagnostics = _extract_diagnostics(error_message)

    real_diagnostics = [d for d in diagnostics if d.level != "note"]
    errors = [d for d in real_diagnostics if d.level == "error"]
    chosen = errors[0] if errors else (real_diagnostics[0] if real_diagnostics else None)

    if chosen is not None:
        # DEBUG: the exact string the matcher will receive (chosen.message),
        # versus the full raw input, so a diff in extraction is visible
        # right at the source rather than inferred from the matcher's miss.
        logger.debug(
            "parse_c_error: extracted message=%r (file=%s, line=%s, level=%s) from input=%r",
            chosen.message,
            chosen.file,
            chosen.line,
            chosen.level,
            error_message,
        )
        return ParsedError(
            raw_message=chosen.message,
            file=chosen.file,
            line=chosen.line,
            column=chosen.column,
            level=chosen.level,
        )

    logger.debug(
        "parse_c_error: no gcc/clang-style diagnostic line found - falling back to raw input=%r",
        error_message,
    )
    return ParsedError(raw_message=error_message.strip())


def parse_error(request: ExplainRequest) -> ParsedError:
    """
    Entry point used by the API layer.

    Currently only supports C. When AUTO is passed we still treat it
    as C for now, since C is the only language implemented so far.
    """
    if request.language in (Language.C, Language.AUTO):
        return parse_c_error(request.error_message)

    # Not reachable in practice today - main.py rejects unsupported
    # languages with an HTTP 400 before this function is ever called.
    # Kept as a safe default for when more languages are wired up.
    return ParsedError(raw_message=request.error_message.strip())
