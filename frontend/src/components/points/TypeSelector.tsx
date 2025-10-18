import { useState, useEffect, useRef } from 'react';
import { getPointTypes } from '../../api/types';
import type { PointType } from '../../types/point';
import { getErrorMessage } from '../../api/client';
import './TypeSelector.css';

interface TypeSelectorProps {
  value?: string;
  onChange: (typeId: string) => void;
  disabled?: boolean;
  required?: boolean;
  label?: string;
  helpText?: string;
}

export default function TypeSelector({
  value,
  onChange,
  disabled = false,
  required = false,
  label = 'Point Type',
  helpText,
}: TypeSelectorProps) {
  const [types, setTypes] = useState<PointType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadTypes();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const loadTypes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPointTypes();

      // Ensure data is an array
      if (!Array.isArray(data)) {
        console.error('getPointTypes returned non-array:', data);
        setError('Invalid response format from server');
        setTypes([]);
        return;
      }

      setTypes(data);

      // If no value is set and we have types, default to the first one (usually "Point")
      if (!value && data.length > 0) {
        onChange(data[0].id);
      }
    } catch (err) {
      console.error('Error loading types:', err);
      setError(getErrorMessage(err));
      setTypes([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="type-selector">
        <label className="type-selector-label">{label}</label>
        <div className="type-selector-loading">Loading types...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="type-selector">
        <label className="type-selector-label">{label}</label>
        <div className="type-selector-error" role="alert">
          Failed to load types: {error}
        </div>
      </div>
    );
  }

  const selectedType = types.find(t => t.id === value);

  const handleSelect = (typeId: string) => {
    onChange(typeId);
    setIsOpen(false);
  };

  return (
    <div className="type-selector" ref={dropdownRef}>
      <label className="type-selector-label">
        {label}
        {required && <span className="required">*</span>}
      </label>

      <div className="type-selector-wrapper">
        <button
          type="button"
          className={`type-selector-button ${isOpen ? 'open' : ''}`}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          {selectedType ? (
            <span className="type-selector-selected">
              {selectedType.icon && selectedType.icon !== '/icons/default.svg' ? (
                selectedType.icon.startsWith('http') || selectedType.icon.startsWith('/') ? (
                  <img
                    src={selectedType.icon}
                    alt=""
                    className="type-icon"
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                ) : (
                  <span className="type-icon-emoji">{selectedType.icon}</span>
                )
              ) : (
                <span className="type-icon-emoji">📍</span>
              )}
              <span>{selectedType.name}</span>
            </span>
          ) : (
            <span className="type-selector-placeholder">Select a type...</span>
          )}
          <span className="type-selector-arrow">▼</span>
        </button>

        {isOpen && (
          <ul className="type-selector-dropdown" role="listbox">
            {Array.isArray(types) && types.map((type) => (
              <li
                key={type.id}
                className={`type-selector-option ${value === type.id ? 'selected' : ''}`}
                onClick={() => handleSelect(type.id)}
                role="option"
                aria-selected={value === type.id}
              >
                {type.icon && type.icon !== '/icons/default.svg' ? (
                  type.icon.startsWith('http') || type.icon.startsWith('/') ? (
                    <img
                      src={type.icon}
                      alt=""
                      className="type-icon"
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  ) : (
                    <span className="type-icon-emoji">{type.icon}</span>
                  )
                ) : (
                  <span className="type-icon-emoji">📍</span>
                )}
                <span className="type-name">{type.name}</span>
                {!type.user && <span className="type-badge">(Base)</span>}
              </li>
            ))}
          </ul>
        )}
      </div>

      {helpText && (
        <small className="type-selector-help">{helpText}</small>
      )}
    </div>
  );
}
