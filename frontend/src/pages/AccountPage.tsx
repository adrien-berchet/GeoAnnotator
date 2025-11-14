/**
 * Account management page.
 *
 * Allows users to manage their username, email, password, and account deletion.
 */

import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useAccount } from "../hooks/useAccount";
import { UsernameField } from "../components/account/UsernameField";
import { EmailChangeForm } from "../components/account/EmailChangeForm";
import { PasswordChangeForm } from "../components/account/PasswordChangeForm";
import { DeleteAccountButton } from "../components/account/DeleteAccountButton";
import "./AccountPage.css";

export function AccountPage() {
  const { user } = useAuth();
  const { account, fetchAccount, isLoading, error } = useAccount();
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  useEffect(() => {
    const loadAccount = async () => {
      try {
        await fetchAccount();
      } catch (err) {
        console.error("Failed to load account:", err);
      } finally {
        setIsInitialLoad(false);
      }
    };

    loadAccount();
  }, [fetchAccount]);

  if (isInitialLoad && isLoading) {
    return (
      <div className="account-page">
        <div className="account-loading">
          <div className="spinner" role="status">
            <span className="visually-hidden">Loading account...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error && !account) {
    return (
      <div className="account-page">
        <div className="account-error">
          <p className="error-message">{error}</p>
          <button className="retry-button" onClick={fetchAccount}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="account-page">
      <div className="account-container">
        <header className="account-header">
          <h1>Account Management</h1>
          <p className="account-subtitle">
            Manage your profile information and account settings
          </p>
        </header>

        <div className="account-content">
          {/* Account Info Section */}
          <section className="account-section">
            <h2>Account Information</h2>
            <div className="account-info">
              <div className="info-item">
                <span className="info-label">Email:</span>
                <span className="info-value">
                  {account?.email || user?.email}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Member since:</span>
                <span className="info-value">
                  {account?.date_joined
                    ? new Date(account.date_joined).toLocaleDateString()
                    : "N/A"}
                </span>
              </div>
            </div>
          </section>

          {/* Username Section */}
          <section className="account-section">
            <h2>Username</h2>
            <p className="section-description">
              Your username is displayed when sharing content with others. It
              must be unique.
            </p>
            <UsernameField currentUsername={account?.username || ""} />
          </section>

          {/* Email Change Section */}
          <section className="account-section">
            <h2>Change Email Address</h2>
            <p className="section-description">
              Request a change to your email address. A confirmation link will
              be sent to the new email address.
            </p>
            <EmailChangeForm currentEmail={account?.email || ""} />
          </section>

          {/* Password Change Section */}
          <section className="account-section">
            <h2>Change Password</h2>
            <p className="section-description">
              Update your password. You'll need to enter your current password
              to confirm the change.
            </p>
            <PasswordChangeForm />
          </section>

          {/* Danger Zone Section */}
          <section className="account-section danger-zone">
            <h2>Danger Zone</h2>
            <p className="section-description danger-description">
              Deleting your account is permanent. All your data will be removed
              30 days after confirmation.
            </p>
            <DeleteAccountButton
              username={account?.username || "your account"}
            />
          </section>
        </div>
      </div>
    </div>
  );
}
