/**
 * Email confirmation page.
 *
 * Handles email change confirmation via token from email link.
 * Requires user to be logged in.
 */

import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { confirmEmail } from "../api/account";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useAuth } from "../hooks/useAuth";

/**
 * Email confirmation page component.
 */
export function EmailConfirmPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    const confirmEmailChange = async () => {
      const token = searchParams.get("token");

      if (!token) {
        setStatus("error");
        setMessage("Invalid confirmation link. Missing token.");
        return;
      }

      if (!user) {
        setStatus("error");
        setMessage(
          "You must be logged in to confirm email change. Please log in and try again.",
        );
        return;
      }

      try {
        const response = await confirmEmail({ token, user_id: user.id });
        setStatus("success");
        setMessage(
          `Email successfully changed to ${response.new_email}! You can now use your new email to log in.`,
        );

        // Redirect to account page after 3 seconds
        setTimeout(() => {
          navigate("/account");
        }, 3000);
      } catch (err) {
        setStatus("error");
        setMessage(getErrorMessage(err));
      }
    };

    confirmEmailChange();
  }, [searchParams, navigate, user]);

  if (status === "loading") {
    return (
      <div className="confirmation-page">
        <LoadingSpinner message="Confirming email change..." />
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
          {status === "success" ? "Email Changed!" : "Confirmation Failed"}
        </h1>

        <p className="confirmation-message">{message}</p>

        {status === "success" ? (
          <p className="confirmation-hint">
            Redirecting to your account page in 3 seconds...
          </p>
        ) : (
          <div className="confirmation-actions">
            <button
              onClick={() => navigate("/account")}
              className="btn-primary"
            >
              Go to Account
            </button>
            <button onClick={() => navigate("/map")} className="btn-secondary">
              Go to Map
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
