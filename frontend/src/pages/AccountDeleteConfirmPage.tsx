/**
 * Account deletion confirmation page.
 *
 * Handles account deletion confirmation via token from email link.
 * Requires user to be logged in.
 */

import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { confirmDeleteAccount } from "../api/account";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useAuth } from "../hooks/useAuth";

/**
 * Account deletion confirmation page component.
 */
export function AccountDeleteConfirmPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    const confirmDeletion = async () => {
      const token = searchParams.get("token");

      if (!token) {
        setStatus("error");
        setMessage("Invalid confirmation link. Missing token.");
        return;
      }

      if (!user) {
        setStatus("error");
        setMessage(
          "You must be logged in to confirm account deletion. Please log in and try again.",
        );
        return;
      }

      try {
        await confirmDeleteAccount({ token, user_id: user.id });
        setStatus("success");
        setMessage(
          "Account deletion scheduled successfully. Your account will be permanently deleted in 30 days. You have been logged out.",
        );

        // Log out and redirect after 5 seconds
        setTimeout(() => {
          logout();
          navigate("/login");
        }, 5000);
      } catch (err) {
        setStatus("error");
        setMessage(getErrorMessage(err));
      }
    };

    confirmDeletion();
  }, [searchParams, navigate, user, logout]);

  if (status === "loading") {
    return (
      <div className="confirmation-page">
        <LoadingSpinner message="Confirming account deletion..." />
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
            ? "Account Deletion Scheduled"
            : "Confirmation Failed"}
        </h1>

        <p className="confirmation-message">{message}</p>

        {status === "success" ? (
          <div className="confirmation-details">
            <p className="confirmation-hint">
              <strong>Important:</strong> You have 30 days to cancel this
              deletion by logging back in.
            </p>
            <p className="confirmation-hint">
              All your data and shares will be permanently removed after 30
              days.
            </p>
            <p className="confirmation-hint">Logging you out in 5 seconds...</p>
          </div>
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
