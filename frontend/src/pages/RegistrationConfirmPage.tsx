/**
 * Registration email confirmation page.
 *
 * Handles email confirmation for new user registration via token from email link.
 * This is a public route (no authentication required).
 */

import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { confirmRegistration } from "../api/auth";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";

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
        setMessage(getErrorMessage(err));
      }
    };

    confirmEmail();
  }, [searchParams, navigate]);

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
          {status === "success"
            ? "Email Confirmed!"
            : "Confirmation Failed"}
        </h1>

        <p className="confirmation-message">{message}</p>

        {status === "success" ? (
          <p className="confirmation-hint">
            Redirecting to login page in 3 seconds...
          </p>
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
