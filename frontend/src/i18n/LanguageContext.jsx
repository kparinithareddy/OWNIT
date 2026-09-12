import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import en from './translations/en';
import hi from './translations/hi';
import te from './translations/te';
import { translationApi } from '../services/api';

export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', nativeLabel: 'English (Default)' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिंदी (Hindi)' },
  { code: 'te', label: 'Telugu', nativeLabel: 'తెలుగు (Telugu)' }
];

const dictionaries = { en, hi, te };

// In-memory client cache for translated dynamic strings
const dynamicClientCache = new Map();

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    try {
      const stored = localStorage.getItem('ownit_language');
      if (stored && dictionaries[stored]) {
        return stored;
      }
      const storedUser = localStorage.getItem('ownit_user');
      if (storedUser) {
        const parsed = JSON.parse(storedUser);
        if (parsed?.preferredLanguage && dictionaries[parsed.preferredLanguage]) {
          return parsed.preferredLanguage;
        }
      }
    } catch {
      // ignore
    }
    return 'en';
  });

  const changeLanguage = useCallback((newLang) => {
    if (dictionaries[newLang]) {
      setLanguageState(newLang);
      localStorage.setItem('ownit_language', newLang);
      document.documentElement.lang = newLang;
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  /**
   * Translates static UI dictionary keys with dynamic variable interpolation.
   * Example: t('warranty.daysRemaining', { days: 12 }) -> "12 days remaining"
   */
  const t = useCallback((key, params = {}, fallback = null) => {
    if (!key) return '';

    const keys = key.split('.');
    let result = dictionaries[language];

    // Traverse dictionary for current language
    for (const k of keys) {
      if (result && typeof result === 'object' && k in result) {
        result = result[k];
      } else {
        result = null;
        break;
      }
    }

    // Fallback to English dictionary if key missing in current language
    if (result === null || result === undefined) {
      let fallbackDict = dictionaries.en;
      for (const k of keys) {
        if (fallbackDict && typeof fallbackDict === 'object' && k in fallbackDict) {
          fallbackDict = fallbackDict[k];
        } else {
          fallbackDict = null;
          break;
        }
      }
      result = fallbackDict;
    }

    // Fallback to explicit fallback string or key itself
    if (result === null || result === undefined) {
      result = fallback !== null ? fallback : key;
    }

    // Interpolate variables if result is a template string
    if (typeof result === 'string' && params && typeof params === 'object') {
      Object.keys(params).forEach((paramKey) => {
        result = result.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), params[paramKey]);
      });
    }

    return result;
  }, [language]);

  /**
   * Translates dynamic user/database text via backend Translation Service.
   * Returns immediately if language is English or cached; otherwise fetches asynchronously.
   */
  const translateDynamic = useCallback(async (text) => {
    if (!text || typeof text !== 'string' || !text.trim() || language === 'en') {
      return text;
    }

    const cacheKey = `${language}:${text}`;
    if (dynamicClientCache.has(cacheKey)) {
      return dynamicClientCache.get(cacheKey);
    }

    try {
      const res = await translationApi.translate(text, language);
      const translated = res.translatedText || text;
      dynamicClientCache.set(cacheKey, translated);
      return translated;
    } catch (err) {
      console.debug('Dynamic translation fallback to original:', err);
      return text;
    }
  }, [language]);

  /**
   * Batch translates a list of dynamic user/database strings.
   */
  const translateBatchDynamic = useCallback(async (texts) => {
    if (!Array.isArray(texts) || texts.length === 0 || language === 'en') {
      return texts;
    }

    const results = [...texts];
    const missingIndices = [];
    const missingTexts = [];

    texts.forEach((txt, idx) => {
      if (!txt || typeof txt !== 'string' || !txt.trim()) {
        return;
      }
      const cacheKey = `${language}:${txt}`;
      if (dynamicClientCache.has(cacheKey)) {
        results[idx] = dynamicClientCache.get(cacheKey);
      } else {
        missingIndices.push(idx);
        missingTexts.push(txt);
      }
    });

    if (missingTexts.length === 0) {
      return results;
    }

    try {
      const res = await translationApi.translateBatch(missingTexts, language);
      const translations = res.translations || missingTexts;
      missingIndices.forEach((origIdx, i) => {
        const tr = translations[i] || texts[origIdx];
        dynamicClientCache.set(`${language}:${texts[origIdx]}`, tr);
        results[origIdx] = tr;
      });
    } catch (err) {
      console.debug('Batch translation fallback to original:', err);
    }

    return results;
  }, [language]);

  const value = {
    language,
    changeLanguage,
    t,
    translateDynamic,
    translateBatchDynamic,
    languages: SUPPORTED_LANGUAGES,
    isHindi: language === 'hi',
    isTelugu: language === 'te',
    isEnglish: language === 'en'
  };

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

/**
 * Reusable React Hook for dynamic text translation.
 * Automatically triggers translation on language switch without page refresh.
 */
export function useLocalizedText(rawText) {
  const { language, translateDynamic } = useLanguage();
  const [localizedText, setLocalizedText] = useState(rawText);

  useEffect(() => {
    let isMounted = true;

    if (!rawText || language === 'en') {
      setLocalizedText(rawText);
      return;
    }

    const cacheKey = `${language}:${rawText}`;
    if (dynamicClientCache.has(cacheKey)) {
      setLocalizedText(dynamicClientCache.get(cacheKey));
      return;
    }

    translateDynamic(rawText).then((translated) => {
      if (isMounted && translated) {
        setLocalizedText(translated);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [rawText, language, translateDynamic]);

  return localizedText || rawText;
}

/**
 * Reusable React Hook for localizing an array of database items (products, warranties, notes).
 */
export function useLocalizedList(items, fieldsToTranslate = ['name', 'description', 'notes']) {
  const { language, translateBatchDynamic } = useLanguage();
  const [localizedItems, setLocalizedItems] = useState(items);

  useEffect(() => {
    let isMounted = true;

    if (!Array.isArray(items) || items.length === 0 || language === 'en') {
      setLocalizedItems(items);
      return;
    }

    // Collect all strings from specified fields
    const textPool = [];
    const mapping = [];

    items.forEach((item, itemIdx) => {
      fieldsToTranslate.forEach((field) => {
        const val = item?.[field];
        if (typeof val === 'string' && val.trim()) {
          textPool.push(val);
          mapping.push({ itemIdx, field });
        }
      });
    });

    if (textPool.length === 0) {
      setLocalizedItems(items);
      return;
    }

    translateBatchDynamic(textPool).then((translatedPool) => {
      if (!isMounted) return;
      const newItems = items.map((it) => ({ ...it }));
      mapping.forEach(({ itemIdx, field }, poolIdx) => {
        newItems[itemIdx][field] = translatedPool[poolIdx];
      });
      setLocalizedItems(newItems);
    });

    return () => {
      isMounted = false;
    };
  }, [items, language, translateBatchDynamic, fieldsToTranslate.join(',')]);

  return localizedItems;
}
