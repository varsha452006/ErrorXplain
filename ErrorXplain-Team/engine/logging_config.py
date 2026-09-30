"""
Logging setup for the ErrorXplain engine.

Configures the root logger once, at application startup, with a
consistent timestamp/level/logger-name/message format. Every other
module simply calls `logging.getLogger(__name__)` and inherits this
configuration - nothing else needs to touch logging.basicConfig.
"""

import logging


def configure_logging(level: str = "INFO") -> None:
    """
    Configure the root logger.

    Safe to call more than once (logging.basicConfig is a no-op if the
    root logger already has handlers), so importing this module twice
    during tests or reloads won't produce duplicate log lines.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
