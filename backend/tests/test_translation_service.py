import pytest
from app.services.translation import (
    translation_service,
    SUPPORTED_LANGUAGES,
    is_supported_language,
    normalize_language_code,
    translation_cache
)


def test_supported_languages_config():
    assert is_supported_language("en") is True
    assert is_supported_language("hi") is True
    assert is_supported_language("te") is True
    assert is_supported_language("fr") is False
    assert is_supported_language("") is False

    assert normalize_language_code("HI") == "hi"
    assert normalize_language_code("te") == "te"
    assert normalize_language_code("invalid") == "en"


def test_token_protection_and_restoration():
    text = "Model WW80T504DAX1TL with S/N 9928-AFX and IMEI 359123456789012 costs ₹42,990.00 on 2025-01-15 for {days} days."
    protected, token_map = translation_service.protect_technical_identifiers(text)

    # Identifiers must not be in protected text
    assert "WW80T504DAX1TL" not in protected
    assert "9928-AFX" not in protected
    assert "359123456789012" not in protected
    assert "₹42,990.00" not in protected
    assert "2025-01-15" not in protected
    assert "{days}" not in protected

    restored = translation_service.restore_technical_identifiers(protected, token_map)
    assert restored == text


@pytest.mark.anyio
async def test_canonical_english_no_translation():
    text = "Active warranty for Samsung TV"
    result = await translation_service.translate_text(text, "en")
    assert result == text


@pytest.mark.anyio
async def test_vocabulary_and_fallback_translation():
    # Vocabulary lookup
    hi_active = await translation_service.translate_text("active", "hi")
    assert hi_active == "सक्रिय"

    te_active = await translation_service.translate_text("active", "te")
    assert te_active == "యాక్టివ్"


@pytest.mark.anyio
async def test_batch_translation():
    texts = ["active", "expired", "Samsung TV Model UA55DU8000"]
    hi_results = await translation_service.translate_many(texts, "hi")
    assert len(hi_results) == 3
    assert hi_results[0] == "सक्रिय"
    assert hi_results[1] == "समाप्त"
    assert "UA55DU8000" in hi_results[2]


def test_cache_mechanism():
    translation_cache.clear()
    translation_cache.set("Sample text", "en", "hi", "नमूना पाठ")
    assert translation_cache.get("Sample text", "en", "hi") == "नमूना पाठ"
    assert translation_cache.get("Sample text", "en", "te") is None
