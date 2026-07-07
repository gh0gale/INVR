import re

# Stage A: Deterministic Scanner Patterns
# These patterns result in an immediate hard-block without calling the LLM.
HIGH_CONFIDENCE_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"exact\s+numerical\s+thresholds", re.IGNORECASE),
    re.compile(r"forget\s+what\s+you\s+were\s+told", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a\s+|an\s+)?", re.IGNORECASE),
    re.compile(r"print\s+out\s+(your\s+)?(internal\s+)?state", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"bypass", re.IGNORECASE),
    
    # Expanded Coverage
    re.compile(r"(social\s+security\s+number|ssn)", re.IGNORECASE), # Basic PII extraction attempt
    re.compile(r"dan\s+mode", re.IGNORECASE), # DAN mode
    re.compile(r"pretend\s+you\s+are", re.IGNORECASE), # Roleplay override
    re.compile(r"act\s+as\s+(a\s+|an\s+)?", re.IGNORECASE), # Roleplay override
    re.compile(r"gate\s+thresholds?", re.IGNORECASE), # internal config reveal
]

# Stage B: Suspicious Patterns
# These patterns don't guarantee injection but are highly suspicious and require an ML classification pass.
SUSPICIOUS_PATTERNS = [
    re.compile(r"tell\s+me\s+a\s+joke", re.IGNORECASE), # Off-topic
    re.compile(r"translate\s+this", re.IGNORECASE), # Attempting to use the LLM as a general tool
    re.compile(r"write\s+a\s+(story|poem|essay)", re.IGNORECASE), # Off-topic
    re.compile(r"what\s+is\s+your\s+(name|purpose)", re.IGNORECASE), # probing
    re.compile(r"developer\s+mode", re.IGNORECASE), # another jailbreak variant
    re.compile(r"unrestricted", re.IGNORECASE),
]
