/**
 * Email change form component.
 */

import { useState } from "react";
import { useAccount } from "../../hooks/useAccount";
import { useLanguage } from "../../contexts/LanguageContext";
import "./EmailChangeForm.css";

interface EmailChangeFormProps {
  currentEmail: string;
}

export function EmailChangeForm({ currentEmail }: EmailChangeFormProps) {
  const { requestEmailChange, isUpdating } = useAccount();
  const { t } = useLanguage();
  const [newEmail, setNewEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    // Basic validation
    if (!newEmail) {
      setError(t("account.email.enterNew", "Please enter a new email address"));
      return;
    }

    if (newEmail === currentEmail) {
      setError(
        t(
          "account.email.mustBeDifferent",
          "New email must be different from current email",
        ),
      );
      return;
    }

    if (!newEmail.includes("@")) {
      setError(
        t("account.email.invalidFormat", "Please enter a valid email address"),
      );
      return;
    }

    try {
      const response = await requestEmailChange({ new_email: newEmail });
      setSuccessMessage(response.detail);
      setNewEmail(""); // Clear form
    } catch {
      setError(
        t(
          "account.email.sendError",
          "Failed to send confirmation email. Please try again.",
        ),
      );
    }
  };

  return (
    <form className="email-change-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="current-email" className="form-label">
          {t("account.email.currentEmail", "Current Email")}
        </label>
        <input
          type="email"
          id="current-email"
          className="form-input"
          value={currentEmail}
          disabled
          aria-label={t(
            "account.email.currentEmailAriaLabel",
            "Current email address",
          )}
        />
      </div>

      <div className="form-group">
        <label htmlFor="new-email" className="form-label">
          {t("account.email.newEmail", "New Email Address")}
        </label>
        <input
          type="email"
          id="new-email"
          className={`form-input ${error ? "input-error" : ""}`}
          value={newEmail}
          onChange={(e) => {
            setNewEmail(e.target.value);
            setError(null);
            setSuccessMessage(null);
          }}
          placeholder={t(
            "account.email.placeholder",
            "Enter new email address",
          )}
          disabled={isUpdating}
          aria-describedby={error ? "email-error" : undefined}
          aria-invalid={!!error}
        />

        {error && (
          <p className="error-message" id="email-error" role="alert">
            {error}
          </p>
        )}

        {successMessage && (
          <div className="success-message" role="status">
            <p className="success-title">
              {t("account.email.successTitle", "✓ Confirmation email sent!")}
            </p>
            <p className="success-text">{successMessage}</p>
            <p className="success-text">
              {t(
                "account.email.expirationNotice",
                "The confirmation link will expire in 30 minutes.",
              )}
            </p>
          </div>
        )}
      </div>

      <button
        type="submit"
        className="submit-button"
        disabled={isUpdating || !newEmail}
      >
        {isUpdating
          ? t("account.email.sending", "Sending...")
          : t("account.email.sendConfirmation", "Send Confirmation Email")}
      </button>
    </form>
  );
}
