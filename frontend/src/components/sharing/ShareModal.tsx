/**
 * Share modal component.
 *
 * Modal for sharing GPS points with other users.
 */

import { useState } from "react";
import type { FormEvent } from "react";
import { createShare } from "../../api/sharing";
import { getErrorMessage } from "../../api/client";
import { PermissionSelector } from "./PermissionSelector";
import type { Permission } from "../../types/sharing";

interface ShareModalProps {
  pointId: string;
  onClose: () => void;
  onSuccess?: () => void;
}

/**
 * Share modal component.
 */
export function ShareModal({ pointId, onClose, onSuccess }: ShareModalProps) {
  const [email, setEmail] = useState("");
  const [permission, setPermission] = useState<Permission>("view");
  const [error, setError] = useState("");
  const [isSharing, setIsSharing] = useState(false);

  /**
   * Validate email format.
   */
  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate email
    if (!email.trim()) {
      setError("Email is required");
      return;
    }

    if (!isValidEmail(email)) {
      setError("Invalid email format");
      return;
    }

    setIsSharing(true);

    try {
      await createShare(pointId, {
        recipient_email: email.trim(),
        permission_level: permission,
      });

      // Reset form
      setEmail("");
      setPermission("view");

      if (onSuccess) {
        onSuccess();
      }

      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSharing(false);
    }
  };

  /**
   * Handle backdrop click.
   */
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleBackdropClick}>
      <div className="modal-container">
        <div className="modal-header">
          <h2>Share Point</h2>
          <button
            className="modal-close-button"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {/* Error display */}
          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          {/* Email input */}
          <div className="form-group">
            <label htmlFor="share-email">User Email *</label>
            <input
              id="share-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter user's email address"
              disabled={isSharing}
              required
              autoFocus
            />
            <small className="form-text">
              The user will receive an invitation email
            </small>
          </div>

          {/* Permission selector */}
          <div className="form-group">
            <label htmlFor="share-permission">Permission Level *</label>
            <PermissionSelector
              value={permission}
              onChange={setPermission}
              disabled={isSharing}
            />
          </div>

          {/* Actions */}
          <div className="modal-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={isSharing}
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={isSharing}>
              {isSharing ? "Sharing..." : "Share Point"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
