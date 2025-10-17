/**
 * Create point modal component.
 *
 * Modal for creating a new GPS point by clicking on the map.
 */

import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { createPoint, getTags } from '../../api/points';
import { getErrorMessage } from '../../api/client';
import type { GPSPoint, Tag } from '../../types/point';
import { TagSelector } from '../common/TagSelector';
import TypeSelector from '../points/TypeSelector';
import './CreatePointModal.css';

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
  const [selectedTypeId, setSelectedTypeId] = useState<string | undefined>();
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [isPublic, setIsPublic] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Load available tags on mount.
   */
  useEffect(() => {
    loadAvailableTags();
  }, []);

  /**
   * Load available tags from API.
   */
  const loadAvailableTags = async () => {
    try {
      const tags = await getTags();
      setAvailableTags(tags);
    } catch (err) {
      console.error('Error loading tags:', err);
    }
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
      // Create point
      const point = await createPoint({
        title: title.trim(),
        description: description.trim() || undefined,
        latitude,
        longitude,
        is_public: isPublic,
        type_id: selectedTypeId,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
      });

      // Reset form
      setTitle('');
      setDescription('');
      setSelectedTypeId(undefined);
      setSelectedTags([]);
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

  return (
    <>
      {/* Backdrop overlay */}
      {isOpen && (
        <div
          className={`create-point-backdrop ${isOpen ? 'open' : ''}`}
          onClick={onClose}
        />
      )}

      {/* Create point drawer */}
      <div className={`create-point-drawer ${isOpen ? 'open' : ''}`} onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <h2>Create New Point</h2>
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
              rows={3}
              disabled={isLoading}
            />
          </div>

          {/* Type selector */}
          <TypeSelector
            value={selectedTypeId}
            onChange={setSelectedTypeId}
            disabled={isLoading}
            label="Point Type"
            helpText="Select the type of point (defaults to 'Point' if not selected)"
          />

          {/* Tags field */}
          <div className="form-group">
            <label htmlFor="tags">Tags</label>
            <TagSelector
              selectedTags={selectedTags}
              availableTags={availableTags}
              onTagsChange={setSelectedTags}
              disabled={isLoading}
            />
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
    </>
  );
}
