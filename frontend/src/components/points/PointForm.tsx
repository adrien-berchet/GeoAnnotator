/**
 * Point form component.
 *
 * Form for editing GPS point with title, description, tags, and visibility.
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { updatePoint } from '../../api/points';
import { searchTags } from '../../api/points';
import { getErrorMessage } from '../../api/client';
import type { GPSPoint, UpdatePointData } from '../../types/point';

interface PointFormProps {
  point: GPSPoint;
  onSuccess: (updatedPoint: GPSPoint) => void;
  onCancel: () => void;
}

/**
 * Point form component.
 */
export function PointForm({ point, onSuccess, onCancel }: PointFormProps) {
  const [title, setTitle] = useState(point.title);
  const [description, setDescription] = useState(point.description || '');
  const [tags, setTags] = useState(point.tags.map(t => t.name).join(', '));
  const [isPublic, setIsPublic] = useState(point.is_public);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Tag autocomplete
  const [tagSuggestions, setTagSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  /**
   * Search for tag suggestions.
   */
  const handleTagInput = async (value: string) => {
    setTags(value);

    // Get the last tag being typed
    const lastTag = value.split(',').pop()?.trim() || '';

    if (lastTag.length >= 2) {
      try {
        const results = await searchTags(lastTag);
        setTagSuggestions(results.map(t => t.name));
        setShowSuggestions(true);
      } catch (err) {
        console.error('Error searching tags:', err);
      }
    } else {
      setShowSuggestions(false);
    }
  };

  /**
   * Handle tag suggestion click.
   */
  const handleSuggestionClick = (suggestion: string) => {
    const tagList = tags.split(',').map(t => t.trim());
    tagList[tagList.length - 1] = suggestion;
    setTags(tagList.join(', ') + ', ');
    setShowSuggestions(false);
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate title
    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    if (title.length > 255) {
      setError('Title must be 255 characters or less');
      return;
    }

    setIsLoading(true);

    try {
      // Parse tags
      const tagList = tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      // Update point
      const updateData: UpdatePointData = {
        title: title.trim(),
        description: description.trim() || undefined,
        is_public: isPublic,
        tags: tagList.length > 0 ? tagList : undefined,
      };

      const updatedPoint = await updatePoint(point.id, updateData);
      onSuccess(updatedPoint);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="point-form-container">
      <form onSubmit={handleSubmit} className="point-form">
        <h2>Edit Point</h2>

        {/* Error display */}
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        {/* Title field */}
        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter point title"
            maxLength={255}
            disabled={isLoading}
            required
          />
        </div>

        {/* Description field */}
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter point description (optional)"
            rows={6}
            disabled={isLoading}
          />
          <small className="form-text">
            You can use HTML for rich text formatting
          </small>
        </div>

        {/* Tags field with autocomplete */}
        <div className="form-group">
          <label htmlFor="tags">Tags</label>
          <div className="autocomplete-wrapper">
            <input
              id="tags"
              type="text"
              value={tags}
              onChange={(e) => handleTagInput(e.target.value)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              onFocus={() => tags.length >= 2 && setShowSuggestions(true)}
              placeholder="Enter tags separated by commas"
              disabled={isLoading}
            />
            {showSuggestions && tagSuggestions.length > 0 && (
              <ul className="autocomplete-suggestions">
                {tagSuggestions.map((suggestion, index) => (
                  <li
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="autocomplete-item"
                  >
                    {suggestion}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <small className="form-text">
            Separate multiple tags with commas. Start typing to see suggestions.
          </small>
        </div>

        {/* Public checkbox */}
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              disabled={isLoading}
            />
            <span>Make this point public</span>
          </label>
          <small className="form-text">
            Public points are visible to everyone
          </small>
        </div>

        {/* Actions */}
        <div className="form-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
