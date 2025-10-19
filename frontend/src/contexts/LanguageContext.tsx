/**
 * Language context for managing application language and translations
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { Language } from '@/utils/i18n';
import {
  translate as translateUtil,
  getInitialLanguage,
  storeLanguage,
  getSupportedLanguages,
} from '@/utils/i18n';
import { getSettings, updateSettings } from '@/api/settings';
import { useAuth } from '@/hooks/useAuth';

interface LanguageContextType {
  language: Language;
  setLanguage: (language: Language) => Promise<void>;
  t: (key: string, fallback?: string) => string;
  supportedLanguages: Language[];
  isLoading: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface LanguageProviderProps {
  children: ReactNode;
}

export function LanguageProvider({ children }: LanguageProviderProps) {
  const { isAuthenticated } = useAuth();
  const [language, setLanguageState] = useState<Language>('en');
  const [isLoading, setIsLoading] = useState(true);
  const supportedLanguages = getSupportedLanguages();

  // Load initial language on mount
  useEffect(() => {
    const loadLanguage = async () => {
      try {
        if (isAuthenticated) {
          // Load from backend if authenticated
          const settings = await getSettings();
          const initialLang = getInitialLanguage(settings.language);
          setLanguageState(initialLang);
          // Ensure localStorage is in sync
          storeLanguage(initialLang);
        } else {
          // Use localStorage or browser language if not authenticated
          const initialLang = getInitialLanguage();
          setLanguageState(initialLang);
        }
      } catch (error) {
        console.error('Error loading language:', error);
        // Fallback to browser/localStorage language
        const initialLang = getInitialLanguage();
        setLanguageState(initialLang);
      } finally {
        setIsLoading(false);
      }
    };

    loadLanguage();
  }, [isAuthenticated]);

  // Update language
  const setLanguage = useCallback(async (newLanguage: Language) => {
    try {
      // Update local state immediately for better UX
      setLanguageState(newLanguage);

      // Store in localStorage
      storeLanguage(newLanguage);

      // If authenticated, also update backend
      if (isAuthenticated) {
        await updateSettings({ language: newLanguage });
      }
    } catch (error) {
      console.error('Error updating language:', error);
      // Even if backend update fails, keep the language change in localStorage
      // This ensures the user preference is saved locally
    }
  }, [isAuthenticated]);

  // Translation function
  const t = useCallback((key: string, fallback?: string) => {
    return translateUtil(language, key, fallback);
  }, [language]);

  const value: LanguageContextType = {
    language,
    setLanguage,
    t,
    supportedLanguages,
    isLoading,
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

/**
 * Hook to use the language context
 * @returns The language context
 * @throws Error if used outside of LanguageProvider
 */
export function useLanguage(): LanguageContextType {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
