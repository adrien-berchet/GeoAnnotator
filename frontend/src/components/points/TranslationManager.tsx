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

export default function TranslationManager({ names, onChange, disabled = false }: TranslationManagerProps) {
  const { t, currentLanguage } = useLanguage();
  const [newLang, setNewLang] = useState('');
  const [newName, setNewName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleAddTranslation = () => {
    setError(null);

    // Validate language code
    if (!newLang.trim()) {
      setError(t('types.languageCodeRequired', 'Language code is required'));
      return;
    }

    const langCode = newLang.trim().toLowerCase();

    if (!isValidLanguageCode(langCode)) {
      setError(t('types.invalidLanguageCode', 'Language code must be 2 lowercase letters (ISO 639-1)'));
      return;
    }

    // Check if translation already exists
    if (names[langCode]) {
      setError(t('types.translationExists', `Translation for '${langCode}' already exists`));
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
      [langCode]: newName.trim()
    });

    // Reset form
    setNewLang('');
    setNewName('');
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
    onChange({
      ...names,
      [langCode]: value
    });
  };

  const validationError = validateNames(names);

  return (
    <div className="translation-manager">
      <h3>{t('types.translations', 'Translations')}</h3>

      {(error || validationError) && (
        <div className="error-message" role="alert">
          {error || validationError}
        </div>
      )}

      {/* Existing translations */}
      <div className="existing-translations">
        {Object.entries(names).map(([lang, name]) => (
          <div key={lang} className="translation-item">
            <div className="translation-lang">
              <strong>{lang}</strong>
              {lang === currentLanguage && (
                <span className="current-lang-badge" title={t('types.currentLanguage', 'Current language')}>
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
              disabled={disabled || Object.keys(names).length <= 1}
              className="btn-icon btn-delete-translation"
              aria-label={t('types.removeTranslation', `Remove ${lang} translation`)}
              title={Object.keys(names).length <= 1 ? t('types.cannotRemoveLastTranslation', 'Cannot remove last translation') : ''}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* Add new translation */}
      <div className="add-translation">
        <h4>{t('types.addTranslation', 'Add Translation')}</h4>
        <div className="add-translation-form">
          <input
            type="text"
            value={newLang}
            onChange={(e) => {
              setNewLang(e.target.value);
              setError(null);
            }}
            placeholder={t('types.languageCode', 'Language code (e.g., en, fr, es)')}
            disabled={disabled}
            maxLength={2}
            className="lang-input"
          />
          <input
            type="text"
            value={newName}
            onChange={(e) => {
              setNewName(e.target.value);
              setError(null);
            }}
            placeholder={t('types.typeName', 'Type name')}
            disabled={disabled}
            maxLength={100}
            className="name-input"
          />
          <button
            type="button"
            onClick={handleAddTranslation}
            disabled={disabled || !newLang.trim() || !newName.trim()}
            className="btn-primary btn-add-translation"
          >
            {t('common.add', 'Add')}
          </button>
        </div>
        <small className="form-help">
          {t('types.languageCodeHelp', 'Use 2-letter ISO 639-1 language codes (e.g., en=English, fr=French, es=Spanish, de=German)')}
        </small>
      </div>
    </div>
  );
}
