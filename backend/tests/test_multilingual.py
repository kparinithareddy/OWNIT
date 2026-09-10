import pytest
from pydantic import ValidationError
from app.schemas.user import UserPreferencesUpdate
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.services.translation_service import translation_service
from app.services.context_builder import build_product_system_context


def test_user_preferences_validation():
    # Valid languages
    pref_en = UserPreferencesUpdate(preferredLanguage="en")
    assert pref_en.preferredLanguage == "en"

    pref_hi = UserPreferencesUpdate(preferredLanguage="hi")
    assert pref_hi.preferredLanguage == "hi"

    pref_te = UserPreferencesUpdate(preferredLanguage="te")
    assert pref_te.preferredLanguage == "te"

    # Invalid language
    with pytest.raises(ValidationError):
        UserPreferencesUpdate(preferredLanguage="invalid_lang")


def test_translation_vocabulary_lookup():
    # Test vocabulary translations
    assert translation_service.translate_text("active", "hi") == "सक्रिय"
    assert translation_service.translate_text("active", "te") == "యాక్టివ్"
    assert translation_service.translate_text("active", "en") == "active"

    assert translation_service.translate_text("confirmed_coverage", "hi") == "पुष्टि किया गया कवरेज"
    assert translation_service.translate_text("confirmed_coverage", "te") == "నిర్ధారించబడిన కవరేజ్"


def test_technical_entity_protection():
    # Verify that model codes, serial numbers, IMEIs, and prices are protected
    text = "Model WW80T504DAX1TL with S/N 9928-AFX and IMEI 359123456789012 costs ₹42,990.00."
    protected, token_map = translation_service.protect_technical_identifiers(text)
    
    assert "WW80T504DAX1TL" not in protected
    assert "9928-AFX" not in protected
    assert "359123456789012" not in protected
    assert "₹42,990.00" not in protected

    restored = translation_service.restore_technical_identifiers(protected, token_map)
    assert restored == text


def test_explanation_templates():
    # English
    en_msg = translation_service.translate_explanation(
        "offline_ai_fallback",
        target_lang="en",
        product_name="Samsung Washing Machine",
        purchase_date="2025-01-15",
        warranty_count=2
    )
    assert "Samsung Washing Machine" in en_msg
    assert "2025-01-15" in en_msg
    assert "Ollama" in en_msg

    # Hindi
    hi_msg = translation_service.translate_explanation(
        "offline_ai_fallback",
        target_lang="hi",
        product_name="Samsung Washing Machine",
        purchase_date="2025-01-15",
        warranty_count=2
    )
    assert "Samsung Washing Machine" in hi_msg
    assert "2025-01-15" in hi_msg
    assert "ऑफ़लाइन मोड" in hi_msg

    # Telugu
    te_msg = translation_service.translate_explanation(
        "offline_ai_fallback",
        target_lang="te",
        product_name="Samsung Washing Machine",
        purchase_date="2025-01-15",
        warranty_count=2
    )
    assert "Samsung Washing Machine" in te_msg
    assert "2025-01-15" in te_msg
    assert "ఆఫ్‌లైన్" in te_msg


def test_context_builder_multilingual_directives():
    mock_product = ProductResponse(
        id="66dbb01234abcd5678ef9012",
        userId="66dbb01234abcd5678ef9099",
        name="Samsung 8kg Front Load",
        brand="Samsung",
        model="WW80T504DAX1TL",
        category="Appliances",
        purchaseDate="2025-01-15",
        price=42990.00,
        quantity=1,
        serialNumber="SN-88992",
        createdAt="2025-01-15T10:00:00Z",
        updatedAt="2025-01-15T10:00:00Z"
    )

    # Hindi prompt
    hi_prompt, _ = build_product_system_context(
        product=mock_product,
        warranties=[],
        documents=[],
        maintenance_records=[],
        recommendations=[],
        language="hi"
    )
    assert "HINDI (हिंदी)" in hi_prompt
    assert "Devanagari" in hi_prompt
    assert "WW80T504DAX1TL" in hi_prompt
    assert "CRITICAL TECHNICAL ENTITY INTEGRITY" in hi_prompt

    # Telugu prompt
    te_prompt, _ = build_product_system_context(
        product=mock_product,
        warranties=[],
        documents=[],
        maintenance_records=[],
        recommendations=[],
        language="te"
    )
    assert "TELUGU (తెలుగు)" in te_prompt
    assert "Telugu script" in te_prompt
    assert "WW80T504DAX1TL" in te_prompt
    assert "CRITICAL TECHNICAL ENTITY INTEGRITY" in te_prompt

    # English prompt
    en_prompt, _ = build_product_system_context(
        product=mock_product,
        warranties=[],
        documents=[],
        maintenance_records=[],
        recommendations=[],
        language="en"
    )
    assert "English" in en_prompt
