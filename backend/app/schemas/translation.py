from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class TranslationRequest(BaseModel):
    text: str = Field(..., max_length=5000, description="Text to translate")
    targetLanguage: str = Field(..., description="Target language code: 'en', 'hi', or 'te'")
    sourceLanguage: Optional[str] = Field(default="en", description="Source language code or 'auto'")


class TranslationResponse(BaseModel):
    translatedText: str = Field(..., description="Translated result with protected technical tokens")
    sourceLanguage: str = Field(..., description="Resolved source language")
    targetLanguage: str = Field(..., description="Resolved target language")
    isCached: Optional[bool] = Field(default=False, description="Whether translation was served from cache")


class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(..., max_length=100, description="List of strings to translate")
    targetLanguage: str = Field(..., description="Target language code: 'en', 'hi', or 'te'")
    sourceLanguage: Optional[str] = Field(default="en", description="Source language code")


class BatchTranslationResponse(BaseModel):
    translations: List[str] = Field(..., description="List of translated strings matching input order")
    targetLanguage: str = Field(..., description="Target language code")
    count: int = Field(..., description="Number of items translated")


class SupportedLanguagesResponse(BaseModel):
    languages: Dict[str, str] = Field(..., description="Map of supported language codes to display names")
    canonicalLanguage: str = Field(default="en", description="Default canonical system language")
