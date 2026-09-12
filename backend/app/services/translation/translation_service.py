"""
Central Translation Orchestrator for OWNIT.
Coordinates:
1. Technical Token Protection (model numbers, IMEIs, serial numbers, dates, prices, placeholders).
2. Central Language Validation & Zero-API for Canonical English.
3. Thread-safe LRU & TTL Caching.
4. Google Cloud Translation API Integration.
5. High-accuracy offline domain dictionary and explanation template fallbacks.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from app.services.translation.language import (
    SUPPORTED_LANGUAGES,
    CANONICAL_LANGUAGE,
    is_supported_language,
    normalize_language_code
)
from app.services.translation.cache import translation_cache
from app.services.translation.google_translate import google_translate_client

logger = logging.getLogger("ownit.services.translation")

# Robust regex to capture technical identifiers:
# Model numbers, Serial numbers, IMEIs, Dates, URLs, Currency amounts, and template placeholders
TECHNICAL_TOKEN_REGEX = re.compile(
    r"(?P<template_var>\{[a-zA-Z0-9_]+\})|"
    r"(?P<imei>\b\d{15}\b)|"
    r"(?P<date>\b\d{4}-\d{2}-\d{2}\b)|"
    r"(?P<currency>₹\s*[\d,]+(?:\.\d{2})?)|"
    r"(?P<url>https?://[^\s]+)|"
    r"(?P<model_serial>\b[A-Z0-9]{2,}[-_/][A-Z0-9-_/]+\b|\b[A-Z]{2,}\d{2,}[A-Z0-9]*\b)"
)

# Known brand names that should remain in standard brand format
KNOWN_BRANDS = [
    "Samsung", "Sony", "LG", "Apple", "Lenovo", "Dell", "HP", "Asus", "Acer", "OnePlus",
    "Xiaomi", "Realme", "Whirlpool", "Bosch", "Panasonic", "Voltas", "Daikin", "Godrej",
    "Haier", "Philips", "Boat", "Noise", "Canon", "Nikon", "JBL", "Sennheiser", "Bose"
]


class TranslationService:
    """
    Central Translation Service used across all OWNIT modules.
    """

    # High-quality offline domain vocabulary for consumer electronics & warranty
    VOCABULARY: Dict[str, Dict[str, str]] = {
        # Warranty Statuses
        "active": {"en": "Active", "hi": "सक्रिय", "te": "యాక్టివ్"},
        "expiring_soon": {"en": "Expiring Soon", "hi": "शीघ्र समाप्त", "te": "త్వరలో ముగుస్తుంది"},
        "expired": {"en": "Expired", "hi": "समाप्त", "te": "గడువు ముగిసింది"},
        "unregistered": {"en": "Unregistered", "hi": "अपंजीकृत", "te": "నమోదు కాలేదు"},
        
        # Coverage Decision Tiers
        "confirmed_coverage": {"en": "Confirmed Coverage", "hi": "पुष्टि किया गया कवरेज", "te": "నిర్ధారించబడిన కవరేజ్"},
        "likely_coverage": {"en": "Likely Covered", "hi": "संभावित कवरेज", "te": "కవర్ అయ్యే అవకాశం ఉంది"},
        "unclear_coverage": {"en": "Unclear / Verification Needed", "hi": "अस्पष्ट / सत्यापन आवश्यक", "te": "అస్పష్టమైనది / ధృవీకరణ అవసరం"},
        "excluded_issue": {"en": "Excluded from Warranty", "hi": "वारंटी से बाहर", "te": "వారంటీ నుండి మినహాయించబడింది"},

        # Standard Actions & Recommendations
        "book_service": {"en": "Book Authorized Service", "hi": "अधिकृत सेवा बुक करें", "te": "అధీకృత సర్వీస్ బుక్ చేయండి"},
        "upload_invoice": {"en": "Upload Purchase Invoice", "hi": "खरीद रसीद अपलोड करें", "te": "కొనుగోలు రసీదును అప్‌లోడ్ చేయండి"},
        "contact_oem": {"en": "Contact Manufacturer Support", "hi": "निर्माता सहायता से संपर्क करें", "te": "తయారీదారు మద్దతును సంప్రదించండి"},

        # Categories
        "appliances": {"en": "Appliances", "hi": "उपकरण", "te": "ఉపకరణాలు"},
        "electronics": {"en": "Electronics", "hi": "इलेक्ट्रॉनिक्स", "te": "ఎలక్ట్రానిక్స్"},
        "mobile": {"en": "Mobile", "hi": "मोबाइल", "te": "మొబైల్"},
        "laptop": {"en": "Laptop", "hi": "लैपटॉप", "te": "ల్యాప్‌టాప్"},
        "tv": {"en": "TV", "hi": "टीवी", "te": "టీవీ"},
        "refrigerator": {"en": "Refrigerator", "hi": "रेफ्रिजरेटर", "te": "రిఫ్రిజిరేటర్"},
        "washing_machine": {"en": "Washing Machine", "hi": "वाशिंग मशीन", "te": "వాషింగ్ మెషిన్"},
        "air_conditioner": {"en": "Air Conditioner", "hi": "एयर कंडीशनर", "te": "ఎయిర్ కండీషనర్"},

        # Sources
        "user_document": {"en": "Uploaded Document", "hi": "अपलोड किया गया दस्तावेज़", "te": "అప్‌లోడ్ చేసిన పత్రం"},
        "official_manufacturer": {"en": "Official Manufacturer Source", "hi": "आधिकारिक निर्माता स्रोत", "te": "అధికారిక తయారీదారు మూలం"},
        "reliable_external": {"en": "Reliable External Source", "hi": "विश्वसनीय बाहरी स्रोत", "te": "విశ్వసనీయ బాహ్య మూలం"},
        "general_knowledge": {"en": "General Knowledge", "hi": "सामान्य ज्ञान", "te": "సాధారణ పరిజ్ఞానం"}
    }

    # Structured explanation templates with dynamic parameters
    EXPLANATION_TEMPLATES: Dict[str, Dict[str, str]] = {
        "offline_ai_fallback": {
            "en": "I am currently in offline mode because the local Ollama LLM is not responding. Based on your records for {product_name}: Purchase Date is {purchase_date}, with {warranty_count} registered warranty component(s). Please ensure Ollama is running (`ollama serve`) for full conversational assistance.",
            "hi": "मैं वर्तमान में ऑफ़लाइन मोड में हूँ क्योंकि स्थानीय Ollama LLM सेवा उपलब्ध नहीं है। {product_name} के लिए आपके रिकॉर्ड के आधार पर: खरीद तिथि {purchase_date} है, और {warranty_count} पंजीकृत वारंटी घटक हैं। पूर्ण संवादी सहायता के लिए कृपया सुनिश्चित करें कि Ollama चल रहा है (`ollama serve`)।",
            "te": "స్థానిక Ollama LLM అందుబాటులో లేనందున నేను ప్రస్తుతం ఆఫ్‌లైన్ మోడ్‌లో ఉన్నాను. {product_name} కోసం మీ రికార్డుల ఆధారంగా: కొనుగోలు తేదీ {purchase_date}, మరియు {warranty_count} నమోదిత వారంటీ కాంపోనెంట్(లు) ఉన్నాయి. సంభాషణ సహాయం కోసం దయచేసి Ollama రన్ అవుతోందని నిర్ధారించుకోండి (`ollama serve`)."
        },
        "notif_warranty_30d": {
            "en": "Reminder: Your {warranty_type} for {product_name} expires in {days} days ({expiry_date}).",
            "hi": "स्मरणपत्र: {product_name} के लिए आपकी {warranty_type} {days} दिनों में ({expiry_date}) समाप्त हो रही है।",
            "te": "రిమైండర్: {product_name} కొరకు మీ {warranty_type} {days} రోజుల్లో ({expiry_date}) గడువు ముగుస్తుంది."
        },
        "notif_warranty_7d": {
            "en": "Urgent: Your {warranty_type} for {product_name} expires in {days} days ({expiry_date}). Action may be needed.",
            "hi": "अत्यावश्यक: {product_name} के लिए आपकी {warranty_type} {days} दिनों में ({expiry_date}) समाप्त हो रही है। तुरंत ध्यान दें।",
            "te": "అత్యవసరం: {product_name} కొరకు మీ {warranty_type} {days} రోజుల్లో ({expiry_date}) గడువు ముగుస్తుంది. చర్య అవసరం కావచ్చు."
        },
        "notif_warranty_0d": {
            "en": "Coverage Ended: Your {warranty_type} for {product_name} expired on {expiry_date}.",
            "hi": "कवरेज समाप्त: {product_name} के लिए आपकी {warranty_type} {expiry_date} को समाप्त हो गई।",
            "te": "కవరేజ్ ముగిసింది: {product_name} కొరకు మీ {warranty_type} {expiry_date} న ముగిసింది."
        },
        "warranty_disclaimer": {
            "en": "According to your uploaded documents and recorded warranty information. Final coverage is determined by the manufacturer/service center.",
            "hi": "आपके अपलोड किए गए दस्तावेज़ों और दर्ज वारंटी जानकारी के अनुसार। अंतिम कवरेज का निर्धारण निर्माता/सेवा केंद्र द्वारा किया जाता है।",
            "te": "మీరు అప్‌లోడ్ చేసిన పత్రాలు మరియు నమోదు చేసిన వారంటీ సమాచారం ప్రకారం. తుది కవరేజ్ తయారీదారు/సర్వీస్ సెంటర్ ద్వారా నిర్ణయించబడుతుంది."
        }
    }

    def protect_technical_identifiers(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replaces technical identifiers (model numbers, serial numbers, IMEIs, dates, prices, template variables)
        with unique placeholder tokens so translation engines do not corrupt or mistranslate them.
        """
        token_map: Dict[str, str] = {}
        counter = 0

        def replacer(match: re.Match) -> str:
            nonlocal counter
            val = match.group(0)
            token = f"__TOKEN_{counter}__"
            token_map[token] = val
            counter += 1
            return token

        protected_text = TECHNICAL_TOKEN_REGEX.sub(replacer, text)
        return protected_text, token_map

    def restore_technical_identifiers(self, text: str, token_map: Dict[str, str]) -> str:
        """
        Restores original technical identifiers from the placeholder map.
        Handles variations introduced by translation engines (spaces around tokens).
        """
        restored = text
        for token, original_val in token_map.items():
            # Direct replace
            restored = restored.replace(token, original_val)
            # Replace spaced token e.g. "__ TOKEN_0 __"
            spaced_token = re.sub(r"([_])", r"\\1", token)
            spaced_pattern = re.compile(re.escape(token).replace("_", r"\s*_\s*"), re.IGNORECASE)
            restored = spaced_pattern.sub(original_val, restored)
        return restored

    def _dictionary_translate(self, text: str, target_lang: str) -> str:
        """
        Applies offline vocabulary and regex word replacements.
        """
        if not text or target_lang == CANONICAL_LANGUAGE:
            return text

        lookup_key = text.strip().lower().replace(" ", "_")
        if lookup_key in self.VOCABULARY and target_lang in self.VOCABULARY[lookup_key]:
            return self.VOCABULARY[lookup_key][target_lang]

        protected_text, token_map = self.protect_technical_identifiers(text)
        translated = protected_text
        for key, lang_map in self.VOCABULARY.items():
            en_term = lang_map.get("en", "")
            target_term = lang_map.get(target_lang, "")
            if en_term and target_term:
                pattern = re.compile(r"\b" + re.escape(en_term) + r"\b", re.IGNORECASE)
                translated = pattern.sub(target_term, translated)

        return self.restore_technical_identifiers(translated, token_map)

    async def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en"
    ) -> str:
        """
        Translates a single string into target_lang.
        Checks cache, validates language, protects tokens, calls Google Translate,
        and falls back cleanly.
        """
        if not text or not str(text).strip():
            return text

        tgt = normalize_language_code(target_lang)
        src = normalize_language_code(source_lang)

        # 1. Canonical English -> Return original without API call
        if tgt == CANONICAL_LANGUAGE or tgt == src:
            return text

        # 2. Check memory cache
        cached = translation_cache.get(text, src, tgt)
        if cached is not None:
            return cached

        # 3. Direct Vocabulary check
        lookup_key = text.strip().lower().replace(" ", "_")
        if lookup_key in self.VOCABULARY and tgt in self.VOCABULARY[lookup_key]:
            res = self.VOCABULARY[lookup_key][tgt]
            translation_cache.set(text, src, tgt, res)
            return res

        # 4. Protect tokens & Call Google Translate
        protected_text, token_map = self.protect_technical_identifiers(text)
        translated_results = await google_translate_client.translate(
            texts=[protected_text],
            target_lang=tgt,
            source_lang=src if src != "en" else None
        )

        translated_text = translated_results[0] if translated_results else None

        # 5. Fallback if Google API did not return a result
        if not translated_text:
            translated_text = self._dictionary_translate(protected_text, tgt)

        # 6. Restore technical tokens
        final_text = self.restore_technical_identifiers(translated_text, token_map)

        # 7. Cache result
        translation_cache.set(text, src, tgt, final_text)
        return final_text

    async def translate_many(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: str = "en"
    ) -> List[str]:
        """
        Batch translates a list of strings efficiently.
        Deduplicates strings, checks cache, batches external requests, and restores order.
        """
        if not texts:
            return []

        tgt = normalize_language_code(target_lang)
        src = normalize_language_code(source_lang)

        if tgt == CANONICAL_LANGUAGE or tgt == src:
            return texts

        results: List[Optional[str]] = [None] * len(texts)
        missing_indices: List[int] = []
        missing_texts: List[str] = []
        token_maps: List[Dict[str, str]] = []

        # 1. Check cache and identify items needing translation
        for idx, t in enumerate(texts):
            if not t or not str(t).strip():
                results[idx] = t
                continue

            cached = translation_cache.get(t, src, tgt)
            if cached is not None:
                results[idx] = cached
                continue

            # Check direct vocabulary
            lookup_key = t.strip().lower().replace(" ", "_")
            if lookup_key in self.VOCABULARY and tgt in self.VOCABULARY[lookup_key]:
                val = self.VOCABULARY[lookup_key][tgt]
                translation_cache.set(t, src, tgt, val)
                results[idx] = val
                continue

            # Needs external or dictionary translation
            protected_text, token_map = self.protect_technical_identifiers(t)
            missing_indices.append(idx)
            missing_texts.append(protected_text)
            token_maps.append(token_map)

        # 2. Batch call Google Translate for missing items
        if missing_texts:
            translated_batch = await google_translate_client.translate(
                texts=missing_texts,
                target_lang=tgt,
                source_lang=src if src != "en" else None
            )

            for i, missing_idx in enumerate(missing_indices):
                orig_text = texts[missing_idx]
                token_map = token_maps[i]
                translated_item = translated_batch[i] if i < len(translated_batch) else None

                if not translated_item:
                    # Dictionary fallback
                    translated_item = self._dictionary_translate(missing_texts[i], tgt)

                final_text = self.restore_technical_identifiers(translated_item, token_map)
                translation_cache.set(orig_text, src, tgt, final_text)
                results[missing_idx] = final_text

        # 3. Ensure no None values remain
        return [r if r is not None else texts[i] for i, r in enumerate(results)]

    def translate_explanation(self, template_key: str, target_lang: str, **kwargs) -> str:
        """
        Renders a structured localized explanation template with formatted variables.
        """
        lang = normalize_language_code(target_lang)
        templates = self.EXPLANATION_TEMPLATES.get(template_key)

        if not templates:
            logger.warning(f"Translation template '{template_key}' not found.")
            return kwargs.get("default", "")

        template_str = templates.get(lang, templates.get("en", ""))
        try:
            return template_str.format(**kwargs)
        except Exception as e:
            logger.error(f"Error formatting translation template '{template_key}' for lang '{lang}': {e}")
            return templates.get("en", "").format(**kwargs)


# Global singleton instance
translation_service = TranslationService()
