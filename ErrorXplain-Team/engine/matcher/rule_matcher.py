"""
Offline rule matching engine.

Takes the parsed error's main message and finds a rule whose
"patterns" list matches it. Each pattern can be written as either:
    - plain text, e.g. "expected ';' before"    -> substring match
    - a regex, e.g. "undeclared .* first use"   -> regex match

Matching is always case-insensitive, since gcc/clang wording casing
can vary slightly between compiler versions.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from parser.error_parser import ParsedError

logger = logging.getLogger(__name__)


class MatchedRule:
    """A rule that successfully matched, ready to be turned into a response."""

    def __init__(self, rule: Dict[str, Any]) -> None:
        self.id: str = rule.get("id", "unknown_rule")
        self.language: str = rule.get("language", "c")
        self.category: str = rule.get("category", "Unknown")
        self.severity: str = rule.get("severity", "Medium")
        self.explanation: str = rule.get("explanation", "")
        self.suggestion: str = rule.get("suggestion", "")


def _pattern_matches(pattern: str, text: str) -> bool:
    """
    Check whether a single pattern matches the given text.

    A pattern is checked BOTH as a plain substring and as a regex - if
    either matches, it counts:
        - Substring check covers plain-text patterns (the common case,
          since Person B mostly writes plain text like "expected ';'").
        - Regex check covers patterns that use real regex syntax.
    Both checks are case-insensitive.
    """
    if pattern.lower() in text.lower():
        return True

    try:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    except re.error:
        # Not valid regex - fine, it was just plain text and the
        # substring check above already covered that case.
        pass

    return False


def match_rule(parsed_error: ParsedError, rules: List[Dict[str, Any]]) -> Optional[MatchedRule]:
    """
    Find the first rule whose patterns match the parsed error text.

    Rules are checked in the order they appear in the JSON file, and
    within a rule, patterns are checked in order. The first pattern
    that matches wins - no scoring, just first good match.

    Returns None if no rule matches, so the caller can decide whether
    to fall back to AI or return the "no match" response.
    """
    text_to_check = parsed_error.raw_message

    # DEBUG: exactly what we're matching against, and every pattern we're
    # about to check it against. Kept at DEBUG (set LOG_LEVEL=DEBUG to see
    # it) because it fires on every request; if the live endpoint and the
    # tests disagree, comparing this line between the two is the fastest
    # way to see whether the matcher is even receiving the string you
    # expect (e.g. a proxy/client mangling quotes, wrong language bucket,
    # or a rules.json that doesn't match what /rules reports).
    logger.debug(
        "match_rule: text_to_check=%r against %d rule(s): %s",
        text_to_check,
        len(rules),
        {rule.get("id", "unknown_rule"): rule.get("patterns", []) for rule in rules},
    )

    for rule in rules:
        for pattern in rule.get("patterns", []):
            if _pattern_matches(pattern, text_to_check):
                logger.debug(
                    "match_rule: matched rule=%s on pattern=%r", rule.get("id", "unknown_rule"), pattern
                )
                return MatchedRule(rule)

    logger.debug("match_rule: no rule matched text_to_check=%r", text_to_check)
    return None
