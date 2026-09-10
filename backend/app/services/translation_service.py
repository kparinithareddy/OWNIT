import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("ownit.services.translation")

# Regex to capture technical identifiers: Model codes, Serial numbers, IMEIs, Dates, URLs, Prices
TECHNICAL_TOKEN_REGEX = re.compile(
    r"(?P<imei>\b\d{15}\b)|"
    r"(?P<date>\b\d{4}-\d{2}-\d{2}\b)|"
    r"(?P<currency>₹\s*[\d,]+(?:\.\d{2})?)|"
    r"(?P<url>https?://[^\s]+)|"
    r"(?P<model_serial>\b[A-Z0-9]{2,}[-_/][A-Z0-9-_/]+\b|\b[A-Z]{2,}\d{2,}[A-Z0-9]*\b)"
)


class BaseTranslationService(ABC):
    """
    Abstract Base Class for translation services.
    Allows swappable translation backends (dictionary, local neural MT, LLM-based, or external APIs).
    """

    @abstractmethod
    def translate_text(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """Translates arbitrary text from source_lang to target_lang."""
        pass

    @abstractmethod
    def translate_explanation(self, template_key: str, target_lang: str, **kwargs) -> str:
        """Translates a structured explanation template into the target language."""
        pass

    def protect_technical_identifiers(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replaces technical identifiers (model numbers, serial numbers, IMEIs, dates, prices)
        with placeholder tokens so translation engines do not corrupt or mistranslate them.
        """
        token_map: Dict[str, str] = {}
        counter = 0

        def replacer(match: re.Match) -> str:
            nonlocal counter
            val = match.group(0)
            token = f"__TECH_TOKEN_{counter}__"
            token_map[token] = val
            counter += 1
            return token

        protected_text = TECHNICAL_TOKEN_REGEX.sub(replacer, text)
        return protected_text, token_map

    def restore_technical_identifiers(self, text: str, token_map: Dict[str, str]) -> str:
        """
        Restores original technical identifiers from the placeholder map.
        """
        restored = text
        for token, original_val in token_map.items():
            restored = restored.replace(token, original_val)
        return restored


class DictionaryTranslationService(BaseTranslationService):
    """
    High-performance, offline dictionary and template-based translation engine
    specifically tuned for consumer electronics, appliance warranties, and lifecycle workflows.
    Supports English ('en'), Hindi ('hi'), and Telugu ('te').
    """

    # Core system phrases and status vocabulary
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

    def translate_text(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """
        Translates text or vocabulary keys. Defaults to English if target_lang is 'en'
        or if translation is not available. Protects technical identifiers during translation.
        """
        if not text or target_lang == "en":
            return text

        lang = target_lang if target_lang in ["hi", "te"] else "en"
        if lang == "en":
            return text

        # 1. Check vocabulary lookup
        lookup_key = text.strip().lower().replace(" ", "_")
        if lookup_key in self.VOCABULARY and lang in self.VOCABULARY[lookup_key]:
            return self.VOCABULARY[lookup_key][lang]

        # 2. Protect technical tokens before translating
        protected_text, token_map = self.protect_technical_identifiers(text)

        # 3. Apply word/phrase dictionary replacements
        translated = protected_text
        for key, lang_map in self.VOCABULARY.items():
            en_term = lang_map.get("en", "")
            target_term = lang_map.get(lang, "")
            if en_term and target_term:
                # Case-insensitive replacement of whole terms
                pattern = re.compile(re.escape(en_term), re.IGNORECASE)
                translated = pattern.sub(target_term, translated)

        # 4. Restore technical tokens safely
        restored = self.restore_technical_identifiers(translated, token_map)
        return restored

    def translate_explanation(self, template_key: str, target_lang: str, **kwargs) -> str:
        """
        Renders a localized template with formatted variables while ensuring
        technical parameters (product names, model codes, dates, numbers) are preserved.
        """
        lang = target_lang if target_lang in ["en", "hi", "te"] else "en"
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
translation_service = DictionaryTranslationService()
