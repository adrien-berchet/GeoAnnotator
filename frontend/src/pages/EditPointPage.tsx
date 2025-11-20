/**
 * Edit point page.
 *
 * Page for editing an existing GPS point.
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { FormEvent } from "react";
import {
  getPoint,
  updatePoint,
  acquireLock,
  releaseLock,
  getTags,
} from "../api/points";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { TagSelector } from "../components/common/TagSelector";
import TypeSelector from "../components/points/TypeSelector";
import type { GPSPoint, Tag } from "../types/point";
import "./EditPointPage.css";

/**
 * Edit point page component.
 */
export function EditPointPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [point, setPoint] = useState<GPSPoint | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [hasLock, setHasLock] = useState(false);

  // Form fields
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [selectedTypeId, setSelectedTypeId] = useState<string | undefined>();
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [isPublic, setIsPublic] = useState(false);

  /**
   * Load available tags from API.
   */
  const loadAvailableTags = async () => {
    try {
      const tags = await getTags();
      setAvailableTags(tags);
    } catch (err) {
      console.error("Error loading tags:", err);
    }
  };

  /**
   * Load point data and acquire editing lock.
   */
  const loadPoint = async () => {
    if (!id) return;

    setIsLoading(true);
    setError("");

    try {
      // Load point data
      const data = await getPoint(id);
      setPoint(data);

      // Initialize form fields
      setTitle(data.title);
      setDescription(data.description || "");
      setLatitude(data.latitude.toString());
      setLongitude(data.longitude.toString());
      setSelectedTypeId(data.type?.id);
      setSelectedTags(data.tags.map((t) => t.name));
      setIsPublic(data.is_public);

      // Try to acquire lock
      try {
        const lockResult = await acquireLock(id);
        // If we get here, lock was acquired successfully
        if (lockResult.locked_by) {
          setHasLock(true);
          setError(""); // Clear any previous errors
        }
      } catch (lockErr: unknown) {
        // Lock acquisition failed
        console.error("Lock acquisition error:", lockErr);

        // Check error status to distinguish between permission and lock issues
        const maybeAxiosError = lockErr as { response?: { status?: number } };
        const status = maybeAxiosError?.response?.status;

        if (status === 403) {
          // Permission denied
          setError(
            "You do not have permission to edit this point. Only users with edit or manage permissions can modify this point.",
          );
        } else if (status === 409) {
          // Point locked by another user
          if (data.editing_lock_user) {
            setError(
              `This point is currently being edited by ${data.editing_lock_user.email}. Please try again later.`,
            );
          } else {
            setError(
              "This point is currently locked by another user. Please try again later.",
            );
          }
        } else {
          // Other error
          const errorMsg = getErrorMessage(lockErr);
          setError(
            errorMsg ||
              "Unable to acquire editing lock. Please try again later.",
          );
        }
        setHasLock(false);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Load point and acquire lock on mount.
   */
  useEffect(() => {
    if (id) {
      loadPoint();
    }
    loadAvailableTags();

    // Release lock on unmount
    return () => {
      if (id && hasLock) {
        releaseLock(id).catch(console.error);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!id || !hasLock) {
      setError("Cannot save: no editing lock");
      return;
    }

    setError("");

    // Validate title
    if (!title.trim()) {
      setError("Title is required");
      return;
    }

    if (title.length > 255) {
      setError("Title must be 255 characters or less");
      return;
    }

    // Validate coordinates
    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);

    if (isNaN(lat) || lat < -90 || lat > 90) {
      setError("Latitude must be between -90 and 90");
      return;
    }

    if (isNaN(lng) || lng < -180 || lng > 180) {
      setError("Longitude must be between -180 and 180");
      return;
    }

    setIsSaving(true);

    try {
      // Update point
      await updatePoint(id, {
        title: title.trim(),
        description: description.trim() || undefined,
        latitude: lat,
        longitude: lng,
        is_public: isPublic,
        type_id: selectedTypeId,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
      });

      // Release lock
      await releaseLock(id);
      setHasLock(false);

      // Navigate back to detail page
      navigate(`/points/${id}`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Handle cancel.
   */
  const handleCancel = async () => {
    if (id && hasLock) {
      try {
        await releaseLock(id);
      } catch (err) {
        console.error("Error releasing lock:", err);
      }
    }
    navigate(`/points/${id}`);
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message="Loading point..." />;
  }

  if (error && !point) {
    return (
      <div className="error-container">
        <h2>Error loading point</h2>
        <p>{error}</p>
        <button onClick={() => navigate("/points")} className="btn-primary">
          Back to Points
        </button>
      </div>
    );
  }

  if (!point || !id) {
    return (
      <div className="error-container">
        <h2>Point not found</h2>
        <button onClick={() => navigate("/points")} className="btn-primary">
          Back to Points
        </button>
      </div>
    );
  }

  return (
    <div className="edit-point-page">
      {/* Header */}
      <div className="edit-point-header">
        <button onClick={handleCancel} className="back-button">
          ← Back to Point
        </button>
        <h1>Edit Point</h1>
      </div>

      {/* Lock warning */}
      {!hasLock && !isLoading && (
        <div className="warning-message">
          {error && error.includes("permission") ? (
            <>
              <strong>⚠️ No Edit Permission</strong>
              <p>
                You do not have permission to edit this point.
                <br />
                Only users with edit or manage permissions can modify this
                point.
              </p>
            </>
          ) : point.editing_lock_user ? (
            <>
              <strong>⚠️ Editing Locked</strong>
              <p>
                This point is currently being edited by{" "}
                <strong>{point.editing_lock_user.email}</strong>.
                <br />
                Please wait for them to finish or try again later.
              </p>
              {point.owner.id === point.editing_lock_user.id && (
                <button
                  onClick={() => loadPoint()}
                  className="btn-secondary"
                  style={{ marginTop: "0.5rem" }}
                >
                  🔄 Try Again
                </button>
              )}
            </>
          ) : (
            <>
              <strong>⚠️ Editing Locked</strong>
              <p>
                Unable to acquire the editing lock. The point may be locked by
                another user.
                <br />
                Changes cannot be saved until you acquire the lock.
              </p>
              <button
                onClick={() => loadPoint()}
                className="btn-secondary"
                style={{ marginTop: "0.5rem" }}
              >
                🔄 Try Again
              </button>
            </>
          )}
        </div>
      )}

      {/* Edit form */}
      <div className="edit-point-form-container">
        <form onSubmit={handleSubmit} className="edit-point-form">
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
              disabled={!hasLock || isSaving}
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
              disabled={!hasLock || isSaving}
            />
          </div>

          {/* Type selector */}
          <TypeSelector
            value={selectedTypeId}
            onChange={setSelectedTypeId}
            disabled={!hasLock || isSaving}
            label="Point Type"
            helpText="Select the type of point"
          />

          {/* Coordinates */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="latitude">Latitude *</label>
              <input
                id="latitude"
                type="number"
                step="any"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                placeholder="Latitude"
                disabled={!hasLock || isSaving}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="longitude">Longitude *</label>
              <input
                id="longitude"
                type="number"
                step="any"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                placeholder="Longitude"
                disabled={!hasLock || isSaving}
                required
              />
            </div>
          </div>

          {/* Tags field */}
          <div className="form-group">
            <label htmlFor="tags">Tags</label>
            <TagSelector
              selectedTags={selectedTags}
              availableTags={availableTags}
              onTagsChange={setSelectedTags}
              disabled={!hasLock || isSaving}
            />
          </div>

          {/* Public checkbox */}
          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                disabled={!hasLock || isSaving}
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
              onClick={handleCancel}
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={!hasLock || isSaving}
            >
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
