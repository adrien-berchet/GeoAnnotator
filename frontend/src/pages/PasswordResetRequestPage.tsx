/**
 * Password reset request page.
 *
 * Allows users to request a password reset email.
 * This is a public route (no authentication required).
 */

import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "../api/auth";
import { getErrorMessage } from "../api/client";
import "./PasswordResetRequestPage.css";

/**
 * Password reset request page component.
 */
export function PasswordResetRequestPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

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

  /**
   * Validate email format.
   */
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    // Validate email
    if (!email) {
      setError("Email is required");
      return;
    }

    if (!validateEmail(email)) {
      setError("Invalid email format");
      return;
    }

    setIsLoading(true);

    try {
      // Call password reset request API
      const response = await requestPasswordReset(email);
      setSuccess(true);
      setError("");
      // Clear email field for security
      setEmail("");
    } catch (err) {
      // Even if there's an error, we show success to prevent email enumeration
      // The backend always returns 200 for security reasons
      setSuccess(true);
      setError("");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="password-reset-container">
      <div className="password-reset-card">
        <h1>Reset Password</h1>

        {!success ? (
          <>
            <p className="password-reset-description">
              Enter your email address and we'll send you a link to reset your
              password.
            </p>

            <form onSubmit={handleSubmit} className="password-reset-form">
              {/* Error display */}
              {error && (
                <div className="alert alert-error" role="alert">
                  {error}
                </div>
              )}

              {/* Email field */}
              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  className="form-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your.email@example.com"
                  disabled={isLoading}
                  autoComplete="email"
                  required
                />
              </div>

              {/* Submit button */}
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isLoading}
              >
                {isLoading ? "Sending..." : "Send Reset Link"}
              </button>
            </form>

            {/* Login link */}
            <div className="form-footer">
              <p>
                Remember your password? <Link to="/login">Back to Login</Link>
              </p>
            </div>
          </>
        ) : (
          <div className="success-message">
            <div className="success-icon">
              <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h2>Check Your Email</h2>
            <p>
              If an account exists with that email address, you'll receive a
              password reset link shortly. Please check your inbox and spam
              folder.
            </p>
            <p className="success-note">
              The link will expire in 24 hours for security reasons.
            </p>
            <div className="success-actions">
              <Link to="/login" className="btn btn-primary">
                Back to Login
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
