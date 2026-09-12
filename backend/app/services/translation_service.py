"""
Backward-compatible wrapper for app.services.translation_service.
Forwards all calls to the modular app.services.translation package.
"""

from app.services.translation import (
    translation_service,
    TranslationService,
    SUPPORTED_LANGUAGES,
    SUPPORTED_LANGUAGE_CODES,
    CANONICAL_LANGUAGE,
    is_supported_language,
    normalize_language_code
)

__all__ = [
    "translation_service",
    "TranslationService",
    "SUPPORTED_LANGUAGES",
    "SUPPORTED_LANGUAGE_CODES",
    "CANONICAL_LANGUAGE",
    "is_supported_language",
    "normalize_language_code"
]
