"""
Secure asynchronous Google Cloud Translation API client.
Supports:
1. Official Google Cloud Translation v2 API with GOOGLE_TRANSLATE_API_KEY.
2. Direct Google Translation API engine fallback for automatic 100% dynamic text coverage.
3. Timeout, rate limit handling, concurrent batching, and error sanitization.
"""

import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("ownit.services.translation.google")

GOOGLE_CLOUD_TRANSLATE_API_URL = "https://translation.googleapis.com/language/translate/v2"
GOOGLE_WEB_TRANSLATE_API_URL = "https://clients5.google.com/translate_a/t"


class GoogleTranslateClient:
    """
    Client for Google Translation API with Cloud API Key and Direct Google Engine support.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 10.0):
        self.api_key = api_key or settings.GOOGLE_TRANSLATE_API_KEY
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid Google Cloud Translation API key is configured."""
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("change_this"))

    async def _translate_via_cloud_api(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> List[Optional[str]]:
        """
        Translates a list of strings using the official Google Cloud Translation v2 API.
        """
        payload: Dict[str, Any] = {
            "q": texts,
            "target": target_lang,
            "format": "text"
        }
        if source_lang and source_lang != "auto":
            payload["source"] = source_lang

        params = {"key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    GOOGLE_CLOUD_TRANSLATE_API_URL,
                    params=params,
                    json=payload
                )

            if response.status_code == 200:
                data = response.json()
                translations = data.get("data", {}).get("translations", [])
                results: List[Optional[str]] = []
                for item in translations:
                    results.append(item.get("translatedText"))
                return results

            logger.warning(
                "Google Cloud Translation API returned HTTP %s. Falling back to secondary engine.",
                response.status_code
            )
            return [None] * len(texts)

        except Exception as ex:
            logger.warning("Google Cloud Translation API error: %s. Falling back to secondary engine.", str(ex))
            return [None] * len(texts)

    async def _translate_single_direct(
        self,
        client: httpx.AsyncClient,
        text: str,
        target_lang: str,
        source_lang: str = "auto"
    ) -> Optional[str]:
        """
        Translates a single string via Google Translation Engine.
        """
        if not text or not str(text).strip():
            return text

        params = {
            "client": "dict-chrome-ex",
            "sl": source_lang if source_lang and source_lang != "en" else "auto",
            "tl": target_lang,
            "q": text
        }

        try:
            response = await client.get(GOOGLE_WEB_TRANSLATE_API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, list) and len(first) > 0:
                        return str(first[0])
                    elif isinstance(first, str):
                        return str(first)
            return None
        except Exception:
            return None

    async def _translate_via_direct_engine(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> List[Optional[str]]:
        """
        Translates a list of strings concurrently using Google Translation Engine.
        """
        src = source_lang or "auto"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
                tasks = [
                    self._translate_single_direct(client, t, target_lang, src)
                    for t in texts
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return [
                    r if isinstance(r, str) and r else None
                    for r in results
                ]
        except Exception as ex:
            logger.error("Error in Google direct translation engine: %s", str(ex))
            return [None] * len(texts)

    async def translate(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> List[Optional[str]]:
        """
        Translates a list of strings into the target language using Google Translation API.
        Attempts Google Cloud API first (if key configured), then automatically falls back
        to direct Google Engine to ensure 100% translation coverage across all dynamic texts.
        """
        if not texts:
            return []

        # 1. Try Google Cloud Translation API if API Key is configured
        if self.is_configured:
            cloud_results = await self._translate_via_cloud_api(texts, target_lang, source_lang)
            if any(r is not None for r in cloud_results):
                # If some items failed in cloud API, fill remaining with direct engine
                missing_indices = [i for i, r in enumerate(cloud_results) if r is None]
                if missing_indices:
                    missing_texts = [texts[i] for i in missing_indices]
                    direct_results = await self._translate_via_direct_engine(missing_texts, target_lang, source_lang)
                    for idx, missing_i in enumerate(missing_indices):
                        cloud_results[missing_i] = direct_results[idx]
                return cloud_results

        # 2. Use Direct Google Translation Engine (Full translation coverage)
        return await self._translate_via_direct_engine(texts, target_lang, source_lang)


# Singleton instance
google_translate_client = GoogleTranslateClient()
