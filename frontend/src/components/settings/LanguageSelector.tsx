/**
 * Language selector component
 */

import './LanguageSelector.css';

interface LanguageSelectorProps {
  value: string;
  onChange: (language: string) => void;
}

function LanguageSelector({ value }: LanguageSelectorProps) {
  const isDisabled = true; // Only English available for now

  return (
    <div className="language-selector">
      <div
        className={`language-option ${value === 'en' ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}`}
        role="radio"
        aria-checked={value === 'en'}
        aria-label="English language"
        aria-disabled={isDisabled}
      >
        <span className="language-label">English</span>
        {isDisabled && (
          <span className="info-icon" aria-label="Only language available">
            ℹ️
          </span>
        )}
      </div>
      {isDisabled && (
        <p className="language-info">More languages coming soon</p>
      )}
    </div>
  );
}

export default LanguageSelector;
