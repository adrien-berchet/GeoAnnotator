/**
 * Delete account button component with confirmation modal.
 */

import { useState } from "react";
import { useAccount } from "../../hooks/useAccount";
import "./DeleteAccountButton.css";

interface DeleteAccountButtonProps {
  username: string;
}

export function DeleteAccountButton({ username }: DeleteAccountButtonProps) {
  const { requestAccountDeletion, isUpdating } = useAccount();
  const [showModal, setShowModal] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const expectedText = "DELETE";

  const handleOpenModal = () => {
    setShowModal(true);
    setConfirmText("");
    setError(null);
    setSuccessMessage(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setConfirmText("");
    setError(null);
  };

  const handleConfirm = async () => {
    if (confirmText !== expectedText) {
      setError(`Please type "${expectedText}" to confirm`);
      return;
    }

    setError(null);

    try {
      const response = await requestAccountDeletion();
      setSuccessMessage(response.detail);

      // Close modal after short delay to show success message
      setTimeout(() => {
        handleCloseModal();
      }, 3000);
    } catch {
      setError("Failed to send deletion confirmation. Please try again.");
    }
  };

  return (
    <>
      <button
        type="button"
        className="delete-account-button"
        onClick={handleOpenModal}
        disabled={isUpdating}
      >
        🗑️ Delete My Account
      </button>

      {showModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>⚠️ Delete Account</h3>
              <button
                className="modal-close"
                onClick={handleCloseModal}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="warning-box">
                <p className="warning-title">This action cannot be undone!</p>
                <p>
                  Deleting your account (<strong>{username}</strong>) will:
                </p>
                <ul>
                  <li>Immediately unshare all your shared content</li>
                  <li>Send a confirmation email to verify this action</li>
                  <li>
                    Permanently delete all your data <strong>30 days</strong>{" "}
                    after email confirmation
                  </li>
                </ul>
              </div>

              <div className="confirm-section">
                <label htmlFor="confirm-delete" className="confirm-label">
                  Type <strong>{expectedText}</strong> to confirm:
                </label>
                <input
                  type="text"
                  id="confirm-delete"
                  className={`confirm-input ${error && confirmText !== expectedText ? "input-error" : ""}`}
                  value={confirmText}
                  onChange={(e) => {
                    setConfirmText(e.target.value);
                    setError(null);
                  }}
                  placeholder={expectedText}
                  disabled={isUpdating}
                  autoComplete="off"
                  aria-describedby={error ? "delete-error" : undefined}
                  aria-invalid={!!error}
                />
              </div>

              {error && (
                <p className="error-message" id="delete-error" role="alert">
                  {error}
                </p>
              )}

              {successMessage && (
                <div className="success-message" role="status">
                  <p className="success-title">✓ Confirmation email sent!</p>
                  <p className="success-text">{successMessage}</p>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="cancel-button"
                onClick={handleCloseModal}
                disabled={isUpdating}
              >
                Cancel
              </button>
              <button
                type="button"
                className="confirm-delete-button"
                onClick={handleConfirm}
                disabled={confirmText !== expectedText || isUpdating}
              >
                {isUpdating ? "Sending..." : "Send Confirmation Email"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
