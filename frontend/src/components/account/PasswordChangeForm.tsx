/**
 * Password change form component.
 */

import { useState } from "react";
import { useAccount } from "../../hooks/useAccount";
import { useLanguage } from "../../contexts/LanguageContext";
import "./PasswordChangeForm.css";

export function PasswordChangeForm() {
  const { updatePassword, isUpdating } = useAccount();
  const { t } = useLanguage();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showPasswords, setShowPasswords] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    // Validation
    if (!oldPassword) {
      setError(
        t(
          "account.password.enterCurrent",
          "Please enter your current password",
        ),
      );
      return;
    }

    if (!newPassword) {
      setError(t("account.password.enterNew", "Please enter a new password"));
      return;
    }

    if (newPassword.length < 8) {
      setError(
        t(
          "account.password.minLength",
          "New password must be at least 8 characters",
        ),
      );
      return;
    }

    if (newPassword !== confirmPassword) {
      setError(t("account.password.noMatch", "New passwords do not match"));
      return;
    }

    if (newPassword === oldPassword) {
      setError(
        t(
          "account.password.mustBeDifferent",
          "New password must be different from current password",
        ),
      );
      return;
    }

    try {
      const response = await updatePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });
      setSuccessMessage(response.detail);

      // Clear form
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      setError(
        t(
          "account.password.updateError",
          "Failed to change password. Please check your current password and try again.",
        ),
      );
    }
  };

  return (
    <form className="password-change-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="old-password" className="form-label">
          {t("account.password.currentPassword", "Current Password")} *
        </label>
        <div className="password-input-wrapper">
          <input
            type={showPasswords ? "text" : "password"}
            id="old-password"
            className={`form-input ${error ? "input-error" : ""}`}
            value={oldPassword}
            onChange={(e) => {
              setOldPassword(e.target.value);
              setError(null);
              setSuccessMessage(null);
            }}
            placeholder={t(
              "account.password.currentPlaceholder",
              "Enter current password",
            )}
            disabled={isUpdating}
            aria-describedby={error ? "password-error" : undefined}
            aria-invalid={!!error}
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="new-password" className="form-label">
          {t("account.password.newPassword", "New Password")} *
        </label>
        <div className="password-input-wrapper">
          <input
            type={showPasswords ? "text" : "password"}
            id="new-password"
            className={`form-input ${error ? "input-error" : ""}`}
            value={newPassword}
            onChange={(e) => {
              setNewPassword(e.target.value);
              setError(null);
              setSuccessMessage(null);
            }}
            placeholder={t(
              "account.password.newPlaceholder",
              "Enter new password (min 8 characters)",
            )}
            disabled={isUpdating}
            minLength={8}
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="confirm-password" className="form-label">
          {t("account.password.confirmPassword", "Confirm New Password")} *
        </label>
        <div className="password-input-wrapper">
          <input
            type={showPasswords ? "text" : "password"}
            id="confirm-password"
            className={`form-input ${error ? "input-error" : ""}`}
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setError(null);
              setSuccessMessage(null);
            }}
            placeholder={t(
              "account.password.confirmPlaceholder",
              "Confirm new password",
            )}
            disabled={isUpdating}
          />
        </div>
      </div>

      <div className="form-checkbox">
        <input
          type="checkbox"
          id="show-passwords"
          checked={showPasswords}
          onChange={(e) => setShowPasswords(e.target.checked)}
        />
        <label htmlFor="show-passwords">
          {t("account.password.showPasswords", "Show passwords")}
        </label>
      </div>

      {error && (
        <p className="error-message" id="password-error" role="alert">
          {error}
        </p>
      )}

      {successMessage && (
        <div className="success-message" role="status">
          <p className="success-title">
            {t(
              "account.password.successTitle",
              "✓ Password changed successfully!",
            )}
          </p>
          <p className="success-text">{successMessage}</p>
          <p className="success-text">
            {t(
              "account.password.reloginNotice",
              "You may need to log in again on other devices.",
            )}
          </p>
        </div>
      )}

      <button
        type="submit"
        className="submit-button"
        disabled={
          isUpdating || !oldPassword || !newPassword || !confirmPassword
        }
      >
        {isUpdating
          ? t("account.password.changing", "Changing...")
          : t("account.password.changeButton", "Change Password")}
      </button>
    </form>
  );
}
