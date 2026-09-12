"""
Central language configuration for OWNIT.
Canonical source of supported language codes and metadata.
"""

from typing import Dict, List

# Supported languages in OWNIT
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "te": "Telugu (తెలుగు)"
}

SUPPORTED_LANGUAGE_CODES: List[str] = list(SUPPORTED_LANGUAGES.keys())

# Default canonical language
CANONICAL_LANGUAGE: str = "en"


def is_supported_language(code: str) -> bool:
    """Validates if a given language code is supported."""
    return bool(code and code.strip().lower() in SUPPORTED_LANGUAGES)


def normalize_language_code(code: str) -> str:
    """Normalizes language code to standard 2-letter ISO code, defaulting to 'en'."""
    if not code:
        return CANONICAL_LANGUAGE
    clean = code.strip().lower()
    return clean if clean in SUPPORTED_LANGUAGES else CANONICAL_LANGUAGE
