import logging
from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.schemas.translation import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    SupportedLanguagesResponse
)
from app.services.translation import (
    translation_service,
    SUPPORTED_LANGUAGES,
    CANONICAL_LANGUAGE,
    normalize_language_code,
    translation_cache
)

logger = logging.getLogger("ownit.api.translation")

router = APIRouter()


@router.get(
    "/languages",
    response_model=SupportedLanguagesResponse,
    summary="Get supported interface languages",
    description="Returns list of all supported language codes ('en', 'hi', 'te') and native names."
)
async def get_supported_languages() -> SupportedLanguagesResponse:
    return SupportedLanguagesResponse(
        languages=SUPPORTED_LANGUAGES,
        canonicalLanguage=CANONICAL_LANGUAGE
    )


@router.post(
    "/translate",
    response_model=TranslationResponse,
    summary="Translate single text block",
    description="Translates user-facing dynamic text with token protection and caching. Requires authentication."
)
async def translate_text(
    payload: TranslationRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> TranslationResponse:
    tgt = normalize_language_code(payload.targetLanguage)
    src = normalize_language_code(payload.sourceLanguage or "en")

    was_cached = translation_cache.get(payload.text, src, tgt) is not None

    translated = await translation_service.translate_text(
        text=payload.text,
        target_lang=tgt,
        source_lang=src
    )

    return TranslationResponse(
        translatedText=translated,
        sourceLanguage=src,
        targetLanguage=tgt,
        isCached=was_cached
    )


@router.post(
    "/batch",
    response_model=BatchTranslationResponse,
    summary="Translate multiple text strings",
    description="Efficient batch translation with deduplication, token protection, and caching. Requires authentication."
)
async def translate_batch(
    payload: BatchTranslationRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> BatchTranslationResponse:
    tgt = normalize_language_code(payload.targetLanguage)
    src = normalize_language_code(payload.sourceLanguage or "en")

    translated_list = await translation_service.translate_many(
        texts=payload.texts,
        target_lang=tgt,
        source_lang=src
    )

    return BatchTranslationResponse(
        translations=translated_list,
        targetLanguage=tgt,
        count=len(translated_list)
    )
