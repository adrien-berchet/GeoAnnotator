/**
 * Create point modal component.
 *
 * Modal for creating a new GPS point by clicking on the map.
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { createPoint } from '../../api/points';
import { getErrorMessage } from '../../api/client';
import type { GPSPoint } from '../../types/point';

interface CreatePointModalProps {
  latitude: number;
  longitude: number;
  isOpen: boolean;
  onClose: () => void;
  onPointCreated: (point: GPSPoint) => void;
}

/**
 * Create point modal component.
 */
export function CreatePointModal({
  latitude,
  longitude,
  isOpen,
  onClose,
  onPointCreated,
}: CreatePointModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

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

      // Create point
      const point = await createPoint({
        title: title.trim(),
        description: description.trim() || undefined,
        latitude,
        longitude,
        is_public: isPublic,
        tags: tagList.length > 0 ? tagList : undefined,
      });

      // Reset form
      setTitle('');
      setDescription('');
      setTags('');
      setIsPublic(false);

      // Notify parent
      onPointCreated(point);
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create New Point</h2>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="create-point-form">
          {/* Error display */}
          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          {/* Coordinates display */}
          <div className="coordinates-display">
            <span>Lat: {latitude.toFixed(6)}</span>
            <span>Lng: {longitude.toFixed(6)}</span>
          </div>

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
              autoFocus
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
              rows={4}
              disabled={isLoading}
            />
          </div>

          {/* Tags field */}
          <div className="form-group">
            <label htmlFor="tags">Tags</label>
            <input
              id="tags"
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Enter tags separated by commas"
              disabled={isLoading}
            />
            <small className="form-text">
              Separate multiple tags with commas (e.g., "hiking, mountain, photo spot")
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
          <div className="modal-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Creating...' : 'Create Point'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
