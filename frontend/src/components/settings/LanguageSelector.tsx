/**
 * Language selector component
 */

import { useLanguage } from "@/contexts/LanguageContext";
import "./LanguageSelector.css";

interface LanguageSelectorProps {
  value: string;
  onChange: (language: string) => void;
}

function LanguageSelector({ value, onChange }: LanguageSelectorProps) {
  const { t } = useLanguage();

  const languages = [
    { code: "en", label: t("language.en", "English") },
    { code: "fr", label: t("language.fr", "French") },
  ];

  return (
    <div
      className="language-selector"
      role="radiogroup"
      aria-label={t("settings.interfaceLanguage", "Interface Language")}
    >
      {languages.map((lang) => (
        <div
          key={lang.code}
          className={`language-option ${value === lang.code ? "selected" : ""}`}
          role="radio"
          aria-checked={value === lang.code}
          aria-label={`${lang.label} language`}
          tabIndex={0}
          onClick={() => onChange(lang.code)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onChange(lang.code);
            }
          }}
        >
          <span className="language-label">{lang.label}</span>
          {value === lang.code && (
            <span className="check-icon" aria-hidden="true">
              ✓
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

export default LanguageSelector;
