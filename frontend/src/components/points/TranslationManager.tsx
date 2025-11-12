/**
 * TranslationManager component for managing multilingual point type names.
 */

import { useState, useEffect } from "react";
import { validateNames } from "../../utils/pointTypeUtils";
import { useLanguage } from "../../contexts/LanguageContext";
import "./TranslationManager.css";

interface TranslationManagerProps {
  names: Record<string, string>;
  onChange: (names: Record<string, string>) => void;
  disabled?: boolean;
}

// Common languages for the selector
const COMMON_LANGUAGES = [
  { code: "en", name: "English" },
  { code: "fr", name: "Français" },
  { code: "es", name: "Español" },
  { code: "de", name: "Deutsch" },
  { code: "it", name: "Italiano" },
  { code: "pt", name: "Português" },
  { code: "nl", name: "Nederlands" },
  { code: "ru", name: "Русский" },
  { code: "zh", name: "中文" },
  { code: "ja", name: "日本語" },
  { code: "ar", name: "العربية" },
  { code: "hi", name: "हिन्दी" },
];

export default function TranslationManager({
  names,
  onChange,
  disabled = false,
}: TranslationManagerProps) {
  // Hooks React et contexte
  const { t, language } = useLanguage();
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedLang, setSelectedLang] = useState("");
  const [newName, setNewName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [currentInputValue, setCurrentInputValue] = useState(
    names[language] ?? "",
  );

  // Variables calculées et handlers
  const availableLanguages = COMMON_LANGUAGES.filter(
    (lang) => !names[lang.code],
  );
  const cleanNames = Object.fromEntries(
    Object.entries(names).filter(([key]) => key && key !== "undefined"),
  );
  const validationError = validateNames(cleanNames);

  const handleUpdateTranslation = (langCode: string, value: string) => {
    if (langCode && langCode !== "undefined") {
      onChange({ ...names, [langCode]: value });
    }
  };

  const handleRemoveTranslation = (langCode: string) => {
    if (Object.keys(names).length <= 1) return;
    const { [langCode]: removed, ...rest } = names;
    onChange(rest);
  };

  const handleAddTranslation = () => {
    setError(null);
    if (!selectedLang) {
      setError(t("types.languageCodeRequired", "Please select a language"));
      return;
    }
    if (names[selectedLang]) {
      setError(
        t(
          "types.translationExists",
          `Translation for '${selectedLang}' already exists`,
        ),
      );
      return;
    }
    if (!newName.trim()) {
      setError(t("types.nameRequired", "Name is required"));
      return;
    }
    onChange({ ...names, [selectedLang]: newName.trim() });
    setSelectedLang("");
    setNewName("");
    setShowAddForm(false);
  };

  const handleCancelAdd = () => {
    setSelectedLang("");
    setNewName("");
    setError(null);
    setShowAddForm(false);
  };

  // Effet pour garder l'input contrôlé sur la langue courante
  useEffect(() => {
    setCurrentInputValue(names[language] ?? "");
  }, [names, language]);

  return (
    <div className="translation-manager">
      <div className="translation-manager-header">
        <h3>{t("common.name", "Name")}</h3>
      </div>

      {error || validationError ? (
        <div className="translation-error" role="alert">
          {error || validationError}
        </div>
      ) : null}

      {/* Champ obligatoire pour la langue courante */}
      <div className="existing-translations">
        <div className="translation-item">
          <select
            value={language || ""}
            onChange={(e) => {
              const newLang = e.target.value;
              if (newLang && newLang !== language) {
                const updatedNames = { ...names };
                updatedNames[newLang] = updatedNames[language] || "";
                delete updatedNames[language];
                onChange(updatedNames);
              }
            }}
            className="language-select"
            style={{ marginRight: "0.75rem", minWidth: "90px" }}
          >
            {COMMON_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.code.toUpperCase()} - {lang.name}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={currentInputValue}
            onChange={(e) => {
              setCurrentInputValue(e.target.value);
              handleUpdateTranslation(language || "", e.target.value);
            }}
            placeholder={t("types.typeName", "Type name")}
            disabled={disabled}
            className="translation-input"
            required
            style={{ flex: 1 }}
          />
        </div>
      </div>

      {/* Bouton pour ajouter une langue supplémentaire */}
      {availableLanguages.length > 0 && !showAddForm ? (
        <div style={{ marginTop: "1rem" }}>
          <button
            type="button"
            onClick={() => setShowAddForm(true)}
            disabled={disabled}
            className="btn-add-language"
          >
            + {t("types.addTranslation", "Add Translation")}
          </button>
        </div>
      ) : null}

      {/* Ajout d'une nouvelle traduction */}
      {showAddForm && availableLanguages.length > 0 ? (
        <div className="add-translation-panel">
          <div className="panel-header">
            <h4>{t("types.addTranslation", "Add Translation")}</h4>
          </div>
          <div className="add-translation-form">
            <div
              className="form-group"
              style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
            >
              <button
                type="button"
                onClick={handleCancelAdd}
                className="btn-close"
                aria-label={t("common.cancel", "Cancel")}
              >
                ✕
              </button>
              <select
                id="language-select"
                value={selectedLang}
                onChange={(e) => {
                  setSelectedLang(e.target.value);
                  setError(null);
                }}
                disabled={disabled}
                className="language-select"
                style={{ minWidth: "90px" }}
                aria-label={t("types.selectLanguage", "Select Language")}
              >
                <option value="">
                  {t("types.chooseLanguage", "-- Choose a language --")}
                </option>
                {availableLanguages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.code.toUpperCase()} - {lang.name}
                  </option>
                ))}
              </select>
              <input
                id="translation-name"
                type="text"
                value={newName}
                onChange={(e) => {
                  setNewName(e.target.value);
                  setError(null);
                }}
                placeholder={t("types.enterTypeName", "Enter type name")}
                disabled={disabled || !selectedLang}
                className="name-input"
                style={{ flex: 1 }}
                aria-label={t("types.typeName", "Type Name")}
              />
              <button
                type="button"
                onClick={handleAddTranslation}
                disabled={disabled || !selectedLang || !newName.trim()}
                className="btn-primary"
              >
                {t("types.add", "Add")}
              </button>
              <button
                type="button"
                onClick={handleCancelAdd}
                className="btn-secondary"
              >
                {t("common.cancel", "Cancel")}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Affichage des autres traductions (hors langue courante) */}
      <div className="existing-translations">
        {Object.entries(cleanNames)
          .filter(([lang]) => lang !== language)
          .map(([lang, name]) => {
            const languageInfo = COMMON_LANGUAGES.find((l) => l.code === lang);
            return (
              <div key={lang} className="translation-item">
                <div className="translation-lang-label">
                  {languageInfo ? (
                    <span className="lang-name">{languageInfo.name}</span>
                  ) : null}
                </div>
                <input
                  type="text"
                  value={typeof name === "string" ? name : ""}
                  onChange={(e) =>
                    handleUpdateTranslation(lang, e.target.value)
                  }
                  placeholder={t("types.typeName", "Type name")}
                  disabled={disabled}
                  className="translation-input"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveTranslation(lang)}
                  disabled={disabled || Object.keys(cleanNames).length <= 1}
                  className="btn-remove"
                  aria-label={t(
                    "types.removeTranslation",
                    `Remove ${lang} translation`,
                  )}
                  title={
                    Object.keys(cleanNames).length <= 1
                      ? t(
                          "types.cannotRemoveLastTranslation",
                          "Cannot remove last translation",
                        )
                      : ""
                  }
                >
                  ✕
                </button>
              </div>
            );
          })}
      </div>

      {availableLanguages.length === 0 && !showAddForm ? (
        <p className="all-languages-added">
          {t("types.allLanguagesAdded", "All common languages have been added")}
        </p>
      ) : null}
    </div>
  );
}
