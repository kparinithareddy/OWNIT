# Dynamic Multilingual Localization Architecture in OWNIT

## 1. Overview
OWNIT provides seamless, reactive, and dynamic localization across all modules for three core languages:
- **English (`en`)** (Canonical Default Language)
- **Hindi (`hi` / हिंदी)**
- **Telugu (`te` / తెలుగు)**

---

## 2. Core Architecture & Data Independence

```
+-------------------------------------------------------------+
|                      React Frontend                         |
|   +-----------------------------------------------------+   |
|   |                  LanguageContext                    |   |
|   |        (selected language: 'en' | 'hi' | 'te')      |   |
|   +-----------------------------------------------------+   |
|         |                                           |       |
|    [Static UI]                               [Dynamic Data] |
|         |                                           |       |
|   i18n dictionaries                     useLocalizedData()  |
|  (en.js, hi.js, te.js)                  useLocalizedText()  |
|                                                     |       |
+-----------------------------------------------------|-------+
                                                      |
                                          POST /api/v1/translation/batch
                                                      |
+-----------------------------------------------------v-------+
|                    FastAPI Backend                          |
|   +-----------------------------------------------------+   |
|   |         Translation Router & Auth Security          |   |
|   +-----------------------------------------------------+   |
|                             |                               |
|   +-----------------------------------------------------+   |
|   |    backend/app/services/translation/                |   |
|   |    • language.py (Supported languages en, hi, te)   |   |
|   |    • cache.py (Thread-safe memory translation cache)|   |
|   |    • google_translate.py (Google Cloud API client)  |   |
|   |    • translation_service.py (Central orchestrator,  |   |
|   |      token protection, dictionary fallback, batch)  |   |
|   +-----------------------------------------------------+   |
|                             |                               |
|        +--------------------+--------------------+          |
|        |                                         |          |
|  [Google Cloud Translation API]          [Fallback Engine]  |
|  (GOOGLE_TRANSLATE_API_KEY)             (Local dictionaries)|
+-------------------------------------------------------------+
```

### No Duplicate Database Storage
- Canonical records in MongoDB (products, warranties, maintenance, service logs, receipts) remain language-independent.
- No duplicate columns such as `productNameHindi` or `warrantyTelugu` are created.
- Translation is strictly a presentation-layer concern.

---

## 3. Technical Token Protection
During translation, technical identifiers are automatically protected with tokens to prevent corruption by translation engines:
- **Model Numbers**: `UA55DU8000`, `WW80T504DAX1TL`
- **Serial Numbers & IMEIs**: `SN-882910`, `359123456789012`
- **Structured Dates**: `2026-09-11`
- **Prices & Currencies**: `₹72,990.00`
- **URLs & Web Addresses**: `https://...`
- **Template Placeholders**: `{days}`, `{product_name}`

---

## 4. Google Cloud Translation Configuration
Set the backend environment variable in `backend/.env`:
```env
GOOGLE_TRANSLATE_API_KEY=your_google_cloud_api_key_here
```
*Note: The API key is stored exclusively on the backend and is never exposed to the frontend, browser, or Git.*

---

## 5. Offline & Error Fallback Strategy
If Google Cloud Translation API is unavailable (missing key, quota exceeded, or network disconnect), OWNIT automatically:
1. Performs offline domain vocabulary & regex term replacement.
2. Falls back to verified template explanations.
3. Displays the original canonical text seamlessly without crashing or displaying blank screens.
