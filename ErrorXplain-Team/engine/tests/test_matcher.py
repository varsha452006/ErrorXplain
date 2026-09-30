"""Tests for the offline rule matcher."""

from matcher.rule_matcher import match_rule
from parser.error_parser import ParsedError

RULES = [
    {
        "id": "c_missing_semicolon",
        "patterns": ["expected ';' before"],
        "category": "Syntax",
        "severity": "Medium",
        "explanation": "...",
        "suggestion": "...",
    },
    {
        "id": "c_undeclared_identifier",
        "patterns": ["undeclared.*first use"],  # regex pattern
        "category": "Reference",
        "severity": "High",
        "explanation": "...",
        "suggestion": "...",
    },
]


def test_plain_text_pattern_matches_case_insensitively():
    parsed = ParsedError(raw_message="EXPECTED ';' BEFORE 'return'")
    matched = match_rule(parsed, RULES)
    assert matched is not None
    assert matched.id == "c_missing_semicolon"


def test_regex_pattern_matches():
    parsed = ParsedError(raw_message="'x' undeclared (first use in this function)")
    matched = match_rule(parsed, RULES)
    assert matched is not None
    assert matched.id == "c_undeclared_identifier"


def test_no_match_returns_none():
    parsed = ParsedError(raw_message="totally unrelated error text")
    assert match_rule(parsed, RULES) is None


def test_first_matching_rule_wins():
    parsed = ParsedError(raw_message="expected ';' before undeclared first use")
    matched = match_rule(parsed, RULES)
    assert matched.id == "c_missing_semicolon"  # first rule in the list
