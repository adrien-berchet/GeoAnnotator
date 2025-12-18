/**
 * Password reset confirmation page.
 *
 * Handles password reset via token from email link.
 * This is a public route (no authentication required).
 */

import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { confirmPasswordReset, requestPasswordReset } from "../api/auth";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import "./PasswordResetConfirmPage.css";

/**
 * Password reset confirmation page component.
 */
export function PasswordResetConfirmPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isTokenInvalid, setIsTokenInvalid] = useState(false);
  const [showResendForm, setShowResendForm] = useState(false);
  const [resendEmail, setResendEmail] = useState("");
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Apply system theme for password reset page (no user is authenticated yet)
  useEffect(() => {
    const applySystemTheme = () => {
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches;
      document.documentElement.setAttribute(
        "data-theme",
        prefersDark ? "dark" : "light",
      );
    };

    applySystemTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = applySystemTheme;
    mediaQuery.addEventListener("change", handler);

    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  // Extract token from URL on mount
  useEffect(() => {
    const tokenParam = searchParams.get("token");

    if (!tokenParam) {
      setIsTokenInvalid(true);
      setError("Invalid password reset link. Missing token.");
    } else {
      setToken(tokenParam);
    }
  }, [searchParams]);

  /**
   * Validate password strength.
   */
  const validatePassword = (password: string): string | null => {
    if (!password) {
      return "Password is required";
    }
    if (password.length < 8) {
      return "Password must be at least 8 characters";
    }
    // Add more validation rules if needed
    return null;
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate passwords
    const passwordError = validatePassword(newPassword);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      await confirmPasswordReset(token, newPassword);
      setSuccess(true);
      setError("");

      // Redirect to login page after 3 seconds
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);

      // Check if the error is due to invalid/expired token
      if (
        errorMessage.toLowerCase().includes("invalid") ||
        errorMessage.toLowerCase().includes("expired")
      ) {
        setIsTokenInvalid(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle resending password reset email.
   */
  const handleResendReset = async (e: FormEvent) => {
    e.preventDefault();

    if (!resendEmail) {
      return;
    }

    setResendLoading(true);

    try {
      await requestPasswordReset(resendEmail);
      setResendSuccess(true);
      setError("");
    } catch (err) {
      // Even if there's an error, we show success to prevent email enumeration
      setResendSuccess(true);
      setError("");
    } finally {
      setResendLoading(false);
    }
  };

  // Show error state if token is missing
  if (isTokenInvalid && !token) {
    return (
      <div className="password-reset-confirm-page">
        <div className="confirmation-card error">
          <div className="confirmation-icon">
            <svg
              className="icon-error"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>

          <h1>Invalid Reset Link</h1>
          <p className="confirmation-message">{error}</p>

          <div className="confirmation-actions">
            <Link to="/reset-password" className="btn-primary">
              Request New Reset Link
            </Link>
            <Link to="/login" className="btn-secondary">
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Show success state
  if (success) {
    return (
      <div className="password-reset-confirm-page">
        <div className="confirmation-card success">
          <div className="confirmation-icon">
            <svg
              className="icon-success"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>

          <h1>Password Reset Successful!</h1>
          <p className="confirmation-message">
            Your password has been successfully updated. You can now log in with
            your new password.
          </p>

          <p className="confirmation-hint">
            Redirecting to login page in 3 seconds...
          </p>

          <div className="confirmation-actions">
            <Link to="/login" className="btn-primary">
              Go to Login Now
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Show password reset form
  return (
    <div className="password-reset-confirm-page">
      <div className="password-reset-card">
        <h1>Set New Password</h1>
        <p className="password-reset-description">
          Please enter your new password below.
        </p>

        <form onSubmit={handleSubmit} className="password-reset-form">
          {/* Error display */}
          {error && (
            <div className="alert alert-error" role="alert">
              {error}
            </div>
          )}

          {/* Show resend option if token is invalid/expired */}
          {isTokenInvalid && !resendSuccess && !showResendForm && (
            <div className="token-expired-notice">
              <p>Your password reset link has expired or is invalid.</p>
              <button
                type="button"
                onClick={() => setShowResendForm(true)}
                className="btn-link"
              >
                Request a new password reset link
              </button>
            </div>
          )}

          {/* Resend form */}
          {showResendForm && !resendSuccess && (
            <div className="resend-form">
              <label htmlFor="resend-email" className="form-label">
                Enter your email to receive a new reset link:
              </label>
              <input
                id="resend-email"
                type="email"
                className="form-input"
                value={resendEmail}
                onChange={(e) => setResendEmail(e.target.value)}
                placeholder="your.email@example.com"
                disabled={resendLoading}
                required
              />
              <div className="resend-actions">
                <button
                  type="button"
                  onClick={handleResendReset}
                  className="btn btn-primary"
                  disabled={resendLoading}
                >
                  {resendLoading ? "Sending..." : "Send Reset Link"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowResendForm(false)}
                  className="btn btn-secondary"
                  disabled={resendLoading}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Resend success message */}
          {resendSuccess && (
            <div className="alert alert-success">
              Check your email! If an account exists with that email, you'll
              receive a new password reset link.
            </div>
          )}

          {/* Password fields - only show if token is valid */}
          {!isTokenInvalid && !showResendForm && (
            <>
              {/* New password field */}
              <div className="form-group">
                <label htmlFor="new-password" className="form-label">
                  New Password
                </label>
                <input
                  id="new-password"
                  type="password"
                  className="form-input"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password (min 8 characters)"
                  disabled={isLoading}
                  autoComplete="new-password"
                  required
                  minLength={8}
                />
              </div>

              {/* Confirm password field */}
              <div className="form-group">
                <label htmlFor="confirm-password" className="form-label">
                  Confirm New Password
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  className="form-input"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  disabled={isLoading}
                  autoComplete="new-password"
                  required
                  minLength={8}
                />
              </div>

              {/* Submit button */}
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isLoading}
              >
                {isLoading ? "Resetting Password..." : "Reset Password"}
              </button>
            </>
          )}
        </form>

        {/* Login link */}
        {!showResendForm && (
          <div className="form-footer">
            <p>
              Remember your password? <Link to="/login">Back to Login</Link>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
