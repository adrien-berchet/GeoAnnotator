/**
 * Tag selector component with autocomplete.
 *
 * Allows selecting existing tags or creating new ones.
 */

import { useState, useEffect, useRef } from 'react';
import type { Tag } from '../../types/point';
import './TagSelector.css';

interface TagSelectorProps {
  selectedTags: string[];
  availableTags: Tag[];
  onTagsChange: (tags: string[]) => void;
  disabled?: boolean;
}

/**
 * Tag selector component.
 */
export function TagSelector({
  selectedTags,
  availableTags,
  onTagsChange,
  disabled = false,
}: TagSelectorProps) {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredTags, setFilteredTags] = useState<Tag[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  /**
   * Filter tags based on input value.
   */
  useEffect(() => {
    if (inputValue.trim()) {
      const query = inputValue.toLowerCase();
      const filtered = availableTags.filter(
        tag =>
          tag.name.toLowerCase().includes(query) &&
          !selectedTags.includes(tag.name)
      );
      setFilteredTags(filtered);
      setShowSuggestions(filtered.length > 0 || inputValue.trim().length > 0);
    } else {
      setFilteredTags([]);
      setShowSuggestions(false);
    }
  }, [inputValue, availableTags, selectedTags]);

  /**
   * Close suggestions when clicking outside.
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  /**
   * Add a tag.
   */
  const addTag = (tagName: string) => {
    const trimmedTag = tagName.trim();
    if (trimmedTag && !selectedTags.includes(trimmedTag)) {
      onTagsChange([...selectedTags, trimmedTag]);
      setInputValue('');
      setShowSuggestions(false);
    }
  };

  /**
   * Remove a tag.
   */
  const removeTag = (tagName: string) => {
    onTagsChange(selectedTags.filter(t => t !== tagName));
  };

  /**
   * Handle input key press.
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (inputValue.trim()) {
        addTag(inputValue);
      }
    } else if (e.key === 'Backspace' && !inputValue && selectedTags.length > 0) {
      // Remove last tag on backspace if input is empty
      removeTag(selectedTags[selectedTags.length - 1]);
    }
  };

  /**
   * Handle tag suggestion click.
   */
  const handleSuggestionClick = (tagName: string) => {
    addTag(tagName);
    inputRef.current?.focus();
  };

  return (
    <div className="tag-selector">
      {/* Selected tags */}
      <div className="selected-tags">
        {selectedTags.map((tag) => (
          <span key={tag} className="tag-pill">
            {tag}
            {!disabled && (
              <button
                type="button"
                className="tag-remove"
                onClick={() => removeTag(tag)}
                aria-label={`Remove ${tag}`}
              >
                ×
              </button>
            )}
          </span>
        ))}

        {/* Input field */}
        <input
          ref={inputRef}
          type="text"
          className="tag-input"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (inputValue.trim()) {
              setShowSuggestions(true);
            }
          }}
          placeholder={selectedTags.length === 0 ? 'Type to search or add tags...' : ''}
          disabled={disabled}
        />
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && !disabled && (
        <div ref={suggestionsRef} className="tag-suggestions">
          {filteredTags.length > 0 ? (
            <>
              <div className="suggestions-header">Existing tags:</div>
              {filteredTags.map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  className="tag-suggestion"
                  onClick={() => handleSuggestionClick(tag.name)}
                >
                  🏷️ {tag.name}
                </button>
              ))}
            </>
          ) : null}

          {/* Option to create new tag */}
          {inputValue.trim() &&
            !availableTags.some(t => t.name.toLowerCase() === inputValue.toLowerCase()) && (
              <>
                {filteredTags.length > 0 && <div className="suggestions-divider" />}
                <button
                  type="button"
                  className="tag-suggestion create-new"
                  onClick={() => handleSuggestionClick(inputValue.trim())}
                >
                  ✨ Create new tag: <strong>{inputValue.trim()}</strong>
                </button>
              </>
            )}
        </div>
      )}

      {/* Help text */}
      <small className="tag-help">
        Type to search existing tags or create new ones. Press Enter to add.
      </small>
    </div>
  );
}
