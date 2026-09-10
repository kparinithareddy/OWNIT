import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import en from './translations/en';
import hi from './translations/hi';
import te from './translations/te';

export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', nativeLabel: 'English (Default)' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिंदी (Hindi)' },
  { code: 'te', label: 'Telugu', nativeLabel: 'తెలుగు (Telugu)' }
];

const dictionaries = { en, hi, te };

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
   * Helper function to translate a key with optional dynamic variable interpolation.
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

  const value = {
    language,
    changeLanguage,
    t,
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
