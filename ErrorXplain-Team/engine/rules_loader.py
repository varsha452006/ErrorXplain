"""
Loads and caches offline rule definitions from JSON files on disk.

Rules are read from disk exactly once, at application startup (see
main.py's lifespan handler calling load_all_rules()), and served from
an in-memory cache on every request after that - no per-request disk
I/O. A missing or corrupt rule file is logged as a WARNING and treated
as zero rules for that language; it never crashes the server.

Person B only edits the JSON files under rules/<language>/rules.json -
this is the only module that reads them.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from config import settings

logger = logging.getLogger(__name__)

# In-memory cache: language -> list of rule dicts.
_rules_cache: Dict[str, List[Dict[str, Any]]] = {}

# Which languages we know how to load rules for, and where their file lives.
# Add an entry here when a new language's rules.json is introduced.
_RULE_FILE_MAP: Dict[str, Path] = {
    "c": settings.RULES_DIR / "c" / "rules.json",
    "python": settings.RULES_DIR / "python" / "rules.json",
    "java": settings.RULES_DIR / "java" / "rules.json",
}


def _read_rule_file(path: Path) -> List[Dict[str, Any]]:
    """
    Read and parse a single rule JSON file.

    Returns an empty list (after logging a WARNING) for any problem -
    a missing file, invalid JSON, or an unexpected shape must never
    crash the server; it just means 0 rules for that language.
    """
    if not path.exists():
        logger.warning(
            "Rule file not found at %s - continuing with 0 rules for this language.", path
        )
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.warning("Rule file %s is not valid JSON (%s) - continuing with 0 rules.", path, exc)
        return []
    except OSError as exc:
        logger.warning("Could not read rule file %s (%s) - continuing with 0 rules.", path, exc)
        return []

    if isinstance(data, dict) and "rules" in data:
        rules = data["rules"]
    elif isinstance(data, list):
        rules = data
    else:
        logger.warning("Rule file %s has an unexpected top-level shape - continuing with 0 rules.", path)
        return []

    if not isinstance(rules, list):
        logger.warning("Rule file %s: 'rules' key is not a list - continuing with 0 rules.", path)
        return []

    return rules


def load_all_rules() -> None:
    """
    Load every configured language's rules from disk into the cache.

    Call once at application startup. Safe to call again later (e.g.
    a future admin "reload rules" endpoint) since it just replaces the
    cache contents.
    """
    for language, path in _RULE_FILE_MAP.items():
        rules = _read_rule_file(path)
        _rules_cache[language] = rules
        logger.info("Loaded %d rule(s) for language '%s' from %s", len(rules), language, path)


def get_rules(language: str) -> List[Dict[str, Any]]:
    """Return the cached rules for a language (empty list if none loaded)."""
    return _rules_cache.get(language, [])


def get_rule_count() -> int:
    """Total number of rules currently cached, across all languages."""
    return sum(len(rules) for rules in _rules_cache.values())


def get_rule_ids(language: str) -> List[str]:
    """Rule IDs for a language - used by the /rules debug endpoint."""
    return [rule.get("id", "unknown_rule") for rule in get_rules(language)]