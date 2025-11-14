/**
 * Username field component with inline validation.
 */

import { useState, useCallback, useEffect } from "react";
import { useAccount } from "../../hooks/useAccount";
import { useAuth } from "../../hooks/useAuth";
import { useLanguage } from "../../contexts/LanguageContext";
import "./UsernameField.css";

interface UsernameFieldProps {
  currentUsername: string;
}

export function UsernameField({ currentUsername }: UsernameFieldProps) {
  const { updateAccountUsername, checkUsername, isUpdating, isValidating } =
    useAccount();
  const { updateUser, user } = useAuth();
  const { t } = useLanguage();
  const [username, setUsername] = useState(currentUsername);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(
    null,
  );

  // Update local state when prop changes
  useEffect(() => {
    setUsername(currentUsername);
  }, [currentUsername]);

  // Debounced validation
  const validateUsernameDebounced = useCallback(
    (value: string) => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }

      // Don't validate if empty or same as current
      if (!value || value === currentUsername) {
        setValidationError(null);
        return;
      }

      const timer = setTimeout(async () => {
        try {
          const result = await checkUsername({ username: value });

          if (!result.valid) {
            setValidationError(
              result.error ||
                t("account.username.invalidUsername", "Invalid username"),
            );
          } else if (result.available === false) {
            setValidationError(
              result.error ||
                t("account.username.usernameTaken", "Username already taken"),
            );
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
    [currentUsername, checkUsername, debounceTimer, t],
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setUsername(value);
    setSuccessMessage(null);
    validateUsernameDebounced(value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setValidationError(null);

    // Don't submit if unchanged
    if (username === currentUsername) {
      return;
    }

    try {
      const updated = await updateAccountUsername({ username: username });
      setSuccessMessage(
        t("account.username.success", "Username updated successfully!"),
      );

      // Update auth context with new username
      if (user) {
        updateUser({ ...user, username: updated.username });
      }
    } catch {
      // Error is set in the hook
    }
  };

  const hasChanges = username !== currentUsername;
  const canSubmit =
    hasChanges && !validationError && !isValidating && !isUpdating;

  return (
    <form className="username-field" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="username" className="form-label">
          {t("account.username.label", "Username")}
        </label>
        <div className="input-with-button">
          <input
            type="text"
            id="username"
            className={`form-input ${validationError ? "input-error" : ""} ${hasChanges && !validationError ? "input-success" : ""}`}
            value={username}
            onChange={handleChange}
            placeholder={t(
              "account.username.placeholder",
              "Enter your username",
            )}
            maxLength={100}
            disabled={isUpdating}
            aria-describedby={validationError ? "username-error" : undefined}
            aria-invalid={!!validationError}
          />
          <button
            type="submit"
            className="update-button"
            disabled={!canSubmit}
            aria-label={t(
              "account.username.updateAriaLabel",
              "Update username",
            )}
          >
            {isUpdating
              ? t("account.username.updating", "Updating...")
              : t("account.username.update", "Update")}
          </button>
        </div>

        {isValidating && (
          <p className="validation-message">
            {t("account.username.checking", "Checking availability...")}
          </p>
        )}

        {validationError && (
          <p className="error-message" id="username-error" role="alert">
            {validationError}
          </p>
        )}

        {successMessage && (
          <p className="success-message" role="status">
            {successMessage}
          </p>
        )}

        <p className="help-text">
          {t(
            "account.username.help",
            "3-100 characters. Letters, numbers, underscore, and hyphen allowed. Displayed when sharing content.",
          )}
        </p>
      </div>
    </form>
  );
}
