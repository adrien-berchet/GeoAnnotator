/**
 * Registration email confirmation page.
 *
 * Handles email confirmation for new user registration via token from email link.
 * This is a public route (no authentication required).
 */

import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { confirmRegistration, resendConfirmation } from "../api/auth";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import "./RegistrationConfirmPage.css";

/**
 * Registration confirmation page component.
 */
export function RegistrationConfirmPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [message, setMessage] = useState("");
  const [isExpired, setIsExpired] = useState(false);
  const [showResendForm, setShowResendForm] = useState(false);
  const [resendEmail, setResendEmail] = useState("");
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  useEffect(() => {
    const confirmEmail = async () => {
      const token = searchParams.get("token");

      if (!token) {
        setStatus("error");
        setMessage("Invalid confirmation link. Missing token.");
        return;
      }

      try {
        const response = await confirmRegistration(token);
        setStatus("success");
        setMessage(
          response.message ||
            "Email confirmed successfully! You can now log in with your account.",
        );

        // Redirect to login page after 3 seconds
        setTimeout(() => {
          navigate("/login");
        }, 3000);
      } catch (err) {
        setStatus("error");
        const errorMessage = getErrorMessage(err);
        setMessage(errorMessage);

        // Check if the error is due to expiration
        if (errorMessage.toLowerCase().includes("expired")) {
          setIsExpired(true);
        }
      }
    };

    confirmEmail();
  }, [searchParams, navigate]);

  const handleResendConfirmation = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!resendEmail) {
      return;
    }

    setResendLoading(true);

    try {
      await resendConfirmation(resendEmail);
      setResendSuccess(true);
      setMessage(
        "Confirmation email sent! Please check your inbox for the new confirmation link.",
      );
    } catch (err) {
      setMessage(getErrorMessage(err));
    } finally {
      setResendLoading(false);
    }
  };

  if (status === "loading") {
    return (
      <div className="confirmation-page">
        <LoadingSpinner message="Confirming your email..." />
      </div>
    );
  }

  return (
    <div className="confirmation-page">
      <div className={`confirmation-card ${status}`}>
        <div className="confirmation-icon">
          {status === "success" ? (
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
          ) : (
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
          )}
        </div>

        <h1>
          {status === "success" ? "Email Confirmed!" : "Confirmation Failed"}
        </h1>

        <p className="confirmation-message">{message}</p>

        {status === "success" ? (
          <p className="confirmation-hint">
            Redirecting to login page in 3 seconds...
          </p>
        ) : resendSuccess ? (
          <div className="confirmation-actions">
            <Link to="/login" className="btn-primary">
              Go to Login
            </Link>
          </div>
        ) : isExpired && !showResendForm ? (
          <div className="confirmation-actions">
            <button
              onClick={() => setShowResendForm(true)}
              className="btn-primary"
            >
              Resend Confirmation Email
            </button>
            <Link to="/login" className="btn-secondary">
              Go to Login
            </Link>
          </div>
        ) : isExpired && showResendForm ? (
          <form onSubmit={handleResendConfirmation} className="resend-form">
            <div className="form-group">
              <label htmlFor="resend-email" className="form-label">
                Enter your email to receive a new confirmation link:
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
            </div>
            <div className="form-actions">
              <button
                type="submit"
                className="btn-primary"
                disabled={resendLoading}
              >
                {resendLoading ? "Sending..." : "Send Confirmation Email"}
              </button>
              <button
                type="button"
                onClick={() => setShowResendForm(false)}
                className="btn-secondary"
                disabled={resendLoading}
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="confirmation-actions">
            <Link to="/login" className="btn-primary">
              Go to Login
            </Link>
            <Link to="/register" className="btn-secondary">
              Register Again
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
