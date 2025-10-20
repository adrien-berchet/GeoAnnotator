/**
 * TranslationManager component for managing multilingual point type names.
 */

import { useState } from 'react';
import { isValidLanguageCode, validateNames } from '../../utils/pointTypeUtils';
import { useLanguage } from '../../contexts/LanguageContext';
import './TranslationManager.css';

interface TranslationManagerProps {
  names: Record<string, string>;
  onChange: (names: Record<string, string>) => void;
  disabled?: boolean;
}

// Common languages for the selector
const COMMON_LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'fr', name: 'Français' },
  { code: 'es', name: 'Español' },
  { code: 'de', name: 'Deutsch' },
  { code: 'it', name: 'Italiano' },
  { code: 'pt', name: 'Português' },
  { code: 'nl', name: 'Nederlands' },
  { code: 'ru', name: 'Русский' },
  { code: 'zh', name: '中文' },
  { code: 'ja', name: '日本語' },
  { code: 'ar', name: 'العربية' },
  { code: 'hi', name: 'हिन्दी' },
];

export default function TranslationManager({ names, onChange, disabled = false }: TranslationManagerProps) {
  const { t, currentLanguage } = useLanguage();
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedLang, setSelectedLang] = useState('');
  const [newName, setNewName] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Get available languages (not already added)
  const availableLanguages = COMMON_LANGUAGES.filter(
    lang => !names[lang.code]
  );

  const handleAddTranslation = () => {
    setError(null);

    // Validate language code
    if (!selectedLang) {
      setError(t('types.languageCodeRequired', 'Please select a language'));
      return;
    }

    // Check if translation already exists
    if (names[selectedLang]) {
      setError(t('types.translationExists', `Translation for '${selectedLang}' already exists`));
      return;
    }

    // Validate name
    if (!newName.trim()) {
      setError(t('types.nameRequired', 'Name is required'));
      return;
    }

    // Add translation
    onChange({
      ...names,
      [selectedLang]: newName.trim()
    });

    // Reset form
    setSelectedLang('');
    setNewName('');
    setShowAddForm(false);
  };

  const handleCancelAdd = () => {
    setSelectedLang('');
    setNewName('');
    setError(null);
    setShowAddForm(false);
  };

  const handleRemoveTranslation = (langCode: string) => {
    // Prevent removing the last translation
    if (Object.keys(names).length <= 1) {
      setError(t('types.cannotRemoveLastTranslation', 'Cannot remove the last translation'));
      return;
    }

    const { [langCode]: removed, ...rest } = names;
    onChange(rest);
    setError(null);
  };

  const handleUpdateTranslation = (langCode: string, value: string) => {
    // Filter out undefined keys and empty values during update
    if (langCode && langCode !== 'undefined') {
      onChange({
        ...names,
        [langCode]: value
      });
    }
  };

  // Clean up any undefined keys in names object
  const cleanNames = Object.fromEntries(
    Object.entries(names).filter(([key, value]) => key && key !== 'undefined')
  );

  const validationError = validateNames(cleanNames);

  return (
    <div className="translation-manager">
      <div className="translation-manager-header">
        <h3>{t('types.translations', 'Translations')}</h3>
        {availableLanguages.length > 0 && !showAddForm && (
          <button
            type="button"
            onClick={() => setShowAddForm(true)}
            disabled={disabled}
            className="btn-add-language"
          >
            + {t('types.addLanguage', 'Add Language')}
          </button>
        )}
      </div>

      {(error || validationError) && (
        <div className="translation-error" role="alert">
          {error || validationError}
        </div>
      )}

      {/* Existing translations */}
      <div className="existing-translations">
        {Object.entries(cleanNames).map(([lang, name]) => {
          const languageInfo = COMMON_LANGUAGES.find(l => l.code === lang);
          return (
            <div key={lang} className="translation-item">
              <div className="translation-lang-label">
                <strong className="lang-code">{lang.toUpperCase()}</strong>
                {languageInfo && (
                  <span className="lang-name">{languageInfo.name}</span>
                )}
                {lang === currentLanguage && (
                  <span className="current-badge" title={t('types.currentLanguage', 'Current language')}>
                    ★
                  </span>
                )}
              </div>
              <input
                type="text"
                value={name}
                onChange={(e) => handleUpdateTranslation(lang, e.target.value)}
                placeholder={t('types.typeName', 'Type name')}
                disabled={disabled}
                className="translation-input"
              />
              <button
                type="button"
                onClick={() => handleRemoveTranslation(lang)}
                disabled={disabled || Object.keys(cleanNames).length <= 1}
                className="btn-remove"
                aria-label={t('types.removeTranslation', `Remove ${lang} translation`)}
                title={Object.keys(cleanNames).length <= 1 ? t('types.cannotRemoveLastTranslation', 'Cannot remove last translation') : ''}
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>

      {/* Add new translation form */}
      {showAddForm && availableLanguages.length > 0 && (
        <div className="add-translation-panel">
          <div className="panel-header">
            <h4>{t('types.addTranslation', 'Add Translation')}</h4>
            <button
              type="button"
              onClick={handleCancelAdd}
              className="btn-close"
              aria-label={t('common.cancel', 'Cancel')}
            >
              ✕
            </button>
          </div>

          <div className="add-translation-form">
            <div className="form-group">
              <label htmlFor="language-select">{t('types.selectLanguage', 'Select Language')}</label>
              <select
                id="language-select"
                value={selectedLang}
                onChange={(e) => {
                  setSelectedLang(e.target.value);
                  setError(null);
                }}
                disabled={disabled}
                className="language-select"
              >
                <option value="">{t('types.chooseLanguage', '-- Choose a language --')}</option>
                {availableLanguages.map(lang => (
                  <option key={lang.code} value={lang.code}>
                    {lang.code.toUpperCase()} - {lang.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="translation-name">{t('types.typeName', 'Type Name')}</label>
              <input
                id="translation-name"
                type="text"
                value={newName}
                onChange={(e) => {
                  setNewName(e.target.value);
                  setError(null);
                }}
                placeholder={t('types.enterTypeName', 'Enter type name')}
                disabled={disabled || !selectedLang}
                maxLength={100}
                className="name-input"
              />
            </div>

            <div className="form-actions">
              <button
                type="button"
                onClick={handleCancelAdd}
                disabled={disabled}
                className="btn-secondary"
              >
                {t('common.cancel', 'Cancel')}
              </button>
              <button
                type="button"
                onClick={handleAddTranslation}
                disabled={disabled || !selectedLang || !newName.trim()}
                className="btn-primary"
              >
                {t('common.add', 'Add')}
              </button>
            </div>
          </div>
        </div>
      )}

      {availableLanguages.length === 0 && !showAddForm && (
        <p className="all-languages-added">
          {t('types.allLanguagesAdded', 'All common languages have been added')}
        </p>
      )}
    </div>
  );
}
