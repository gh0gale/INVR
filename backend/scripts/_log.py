"""Console logging for the Engine Room scripts.

Audit finding NEW-BE-14: these scripts used `print()`. That was defensible while
they were only run by a human at a terminal, but `grade_ledger` and
`analyze_drift` also run unattended in GitHub Actions, where a bare print has no
timestamp, no level, and no way to be filtered or raised to an alert.

The format stays deliberately plain - the message and nothing else at INFO - so
terminal output reads exactly as it did before. Warnings and errors get a level
prefix, which is the whole point: a failed grade should be visibly different
from a progress line when someone scans a CI log.
"""
import io
import logging
import sys


class _LevelFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if record.levelno >= logging.WARNING:
            return f"{record.levelname}: {message}"
        return message


def _utf8_stdout():
    """stdout that will not raise on a non-ASCII character.

    These scripts print emoji status markers. `print()` tolerated that because
    Python replaces unencodable characters on the console; a logging
    StreamHandler does not, and on a Windows cp1252 pipe - which is exactly what
    GitHub Actions and `subprocess.run(capture_output=True)` give you - every
    such line raised UnicodeEncodeError inside the handler and printed a
    traceback instead of the message.

    Falls back to the raw stream if stdout has no buffer, as under pytest's
    capture.
    """
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        return sys.stdout
    return io.TextIOWrapper(buffer, encoding="utf-8", errors="replace", line_buffering=True)


def get_logger(name: str) -> logging.Logger:
    """A console logger that prints like `print` but carries a level."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(_utf8_stdout())
        handler.setFormatter(_LevelFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
