"""
Translation module package exports.
"""

from app.services.translation.language import (
    SUPPORTED_LANGUAGES,
    SUPPORTED_LANGUAGE_CODES,
    CANONICAL_LANGUAGE,
    is_supported_language,
    normalize_language_code
)
from app.services.translation.cache import translation_cache, TranslationCache
from app.services.translation.google_translate import google_translate_client, GoogleTranslateClient
from app.services.translation.translation_service import translation_service, TranslationService

__all__ = [
    "SUPPORTED_LANGUAGES",
    "SUPPORTED_LANGUAGE_CODES",
    "CANONICAL_LANGUAGE",
    "is_supported_language",
    "normalize_language_code",
    "translation_cache",
    "TranslationCache",
    "google_translate_client",
    "GoogleTranslateClient",
    "translation_service",
    "TranslationService"
]
