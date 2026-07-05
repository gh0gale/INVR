import re
import logging

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for zero-latency Stage A scanning
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"exact\s+numerical\s+thresholds", re.IGNORECASE),
    re.compile(r"forget\s+what\s+you\s+were\s+told", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a\s+|an\s+)?", re.IGNORECASE),
    re.compile(r"print\s+out\s+(your\s+)?(internal\s+)?state", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"bypass", re.IGNORECASE)
]

def check_input_safety(user_message: str) -> tuple[bool, str]:
    """
    Stage A: Deterministic Scanner.
    Returns (is_safe: bool, reason: str).
    """
    for pattern in INJECTION_PATTERNS:
        if pattern.search(user_message):
            logger.warning("Guardrail Block Triggered: Matched injection pattern.")
            return False, "I cannot fulfill this request. I am restricted to providing educational financial analysis based on the quantitative engine's telemetry."
            
    return True, ""