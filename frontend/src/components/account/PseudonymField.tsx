/**
 * Pseudonym field component with inline validation.
 */

import { useState, useCallback, useEffect } from "react";
import { useAccount } from "../../hooks/useAccount";
import { useAuth } from "../../hooks/useAuth";
import "./PseudonymField.css";

interface PseudonymFieldProps {
  currentPseudonym: string;
}

export function PseudonymField({ currentPseudonym }: PseudonymFieldProps) {
  const { updateAccountUsername, checkUsername, isUpdating, isValidating } =
    useAccount();
  const { updateUser, user } = useAuth();
  const [pseudonym, setPseudonym] = useState(currentPseudonym);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(
    null,
  );

  // Update local state when prop changes
  useEffect(() => {
    setPseudonym(currentPseudonym);
  }, [currentPseudonym]);

  // Debounced validation
  const validatePseudonymDebounced = useCallback(
    (value: string) => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }

      // Don't validate if empty or same as current
      if (!value || value === currentPseudonym) {
        setValidationError(null);
        return;
      }

      const timer = setTimeout(async () => {
        try {
          const result = await checkUsername({ username: value });

          if (!result.valid) {
            setValidationError(result.error || "Invalid pseudonym");
          } else if (result.available === false) {
            setValidationError(result.error || "Pseudonym already taken");
          } else {
            setValidationError(null);
          }
        } catch {
          // Validation error - don't show to user, they'll see it on submit
          setValidationError(null);
        }
      }, 500); // 500ms debounce

      setDebounceTimer(timer);
    },
    [currentPseudonym, checkUsername, debounceTimer],
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPseudonym(value);
    setSuccessMessage(null);
    validatePseudonymDebounced(value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setValidationError(null);

    // Don't submit if unchanged
    if (pseudonym === currentPseudonym) {
      return;
    }

    try {
      const updated = await updateAccountUsername({ username: pseudonym });
      setSuccessMessage("Pseudonym updated successfully!");

      // Update auth context with new pseudonym
      if (user) {
        updateUser({ ...user, username: updated.username });
      }
    } catch {
      // Error is set in the hook
    }
  };

  const hasChanges = pseudonym !== currentPseudonym;
  const canSubmit =
    hasChanges && !validationError && !isValidating && !isUpdating;

  return (
    <form className="pseudonym-field" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="pseudonym" className="form-label">
          Pseudonym
        </label>
        <div className="input-with-button">
          <input
            type="text"
            id="pseudonym"
            className={`form-input ${validationError ? "input-error" : ""} ${hasChanges && !validationError ? "input-success" : ""}`}
            value={pseudonym}
            onChange={handleChange}
            placeholder="Enter your pseudonym"
            maxLength={99}
            disabled={isUpdating}
            aria-describedby={validationError ? "pseudonym-error" : undefined}
            aria-invalid={!!validationError}
          />
          <button
            type="submit"
            className="update-button"
            disabled={!canSubmit}
            aria-label="Update pseudonym"
          >
            {isUpdating ? "Updating..." : "Update"}
          </button>
        </div>

        {isValidating && (
          <p className="validation-message">Checking availability...</p>
        )}

        {validationError && (
          <p className="error-message" id="pseudonym-error" role="alert">
            {validationError}
          </p>
        )}

        {successMessage && (
          <p className="success-message" role="status">
            {successMessage}
          </p>
        )}

        <p className="help-text">
          1-99 characters, no spaces. Displayed when sharing content.
        </p>
      </div>
    </form>
  );
}
