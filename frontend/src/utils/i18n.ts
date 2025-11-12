/**
 * Internationalization utility functions
 */

import en from "@/assets/i18n/en.json";
import fr from "@/assets/i18n/fr.json";

export type Language = "en" | "fr";
export type TranslationKey = string;

interface Translations {
  [key: string]: string | Translations;
}

const translations: Record<Language, Translations> = {
  en,
  fr,
};

const SUPPORTED_LANGUAGES: Language[] = ["en", "fr"];
const DEFAULT_LANGUAGE: Language = "en";
const STORAGE_KEY = "user_language";

/**
 * Get the browser's preferred language
 * @returns The browser language code or default language
 */
export function getBrowserLanguage(): Language {
  const browserLang = navigator.language.split("-")[0] as Language;
  return SUPPORTED_LANGUAGES.includes(browserLang)
    ? browserLang
    : DEFAULT_LANGUAGE;
}

/**
 * Get the stored language preference from localStorage
 * @returns The stored language or null if not found
 */
export function getStoredLanguage(): Language | null {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored && SUPPORTED_LANGUAGES.includes(stored as Language)
    ? (stored as Language)
    : null;
}

/**
 * Store language preference in localStorage
 * @param language - The language to store
 */
export function storeLanguage(language: Language): void {
  localStorage.setItem(STORAGE_KEY, language);
}

/**
 * Get the initial language based on user preference, backend setting, or browser language
 * @param backendLanguage - The language from backend user preferences (if authenticated)
 * @returns The language to use
 */
export function getInitialLanguage(backendLanguage?: string): Language {
  // Priority: 1. Backend preference (if authenticated), 2. localStorage, 3. Browser language
  if (
    backendLanguage &&
    SUPPORTED_LANGUAGES.includes(backendLanguage as Language)
  ) {
    return backendLanguage as Language;
  }

  const storedLanguage = getStoredLanguage();
  if (storedLanguage) {
    return storedLanguage;
  }

  return getBrowserLanguage();
}

/**
 * Get a translation by key path (e.g., "settings.title")
 * @param language - The language to use
 * @param key - The translation key path
 * @param fallback - Optional fallback text if translation not found
 * @returns The translated text
 */
export function translate(
  language: Language,
  key: TranslationKey,
  fallback?: string,
): string {
  const keys = key.split(".");
  let current: Translations | string =
    translations[language] || translations[DEFAULT_LANGUAGE];

  for (const k of keys) {
    if (typeof current === "object" && k in current) {
      current = current[k];
    } else {
      // Fallback to English if key not found in selected language
      if (language !== DEFAULT_LANGUAGE) {
        return translate(DEFAULT_LANGUAGE, key, fallback);
      }
      // If not found even in English, return fallback or key
      return fallback || key;
    }
  }

  return typeof current === "string" ? current : fallback || key;
}

/**
 * Get all supported languages
 * @returns Array of supported language codes
 */
export function getSupportedLanguages(): Language[] {
  return [...SUPPORTED_LANGUAGES];
}

/**
 * Check if a language is supported
 * @param language - The language code to check
 * @returns True if the language is supported
 */
export function isLanguageSupported(language: string): language is Language {
  return SUPPORTED_LANGUAGES.includes(language as Language);
}
