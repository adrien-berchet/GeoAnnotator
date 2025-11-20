/**
 * Share Panel Component
 *
 * Slide-in drawer for sharing points with friends
 */

import { useState, useEffect } from "react";
import { getFriends, type Friend } from "../../api/friends";
import { getErrorMessage } from "../../api/client";
import "./SharePanel.css";

interface SharePanelProps {
  isOpen: boolean;
  selectedPointIds: string[];
  onClose: () => void;
  onShare: (usernames: string[], permissionLevel: string) => void;
}

export function SharePanel({
  isOpen,
  selectedPointIds,
  onClose,
  onShare,
}: SharePanelProps) {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [selectedFriends, setSelectedFriends] = useState<string[]>([]);
  const [newUsernames, setNewUsernames] = useState("");
  const [permissionLevel, setPermissionLevel] = useState<
    "view" | "edit" | "manage"
  >("view");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen) {
      loadFriends();
    }
  }, [isOpen]);

  const loadFriends = async () => {
    setIsLoading(true);
    setError("");

    try {
      const data = await getFriends();
      setFriends(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleFriend = (username: string) => {
    setSelectedFriends((prev) =>
      prev.includes(username)
        ? prev.filter((u) => u !== username)
        : [...prev, username],
    );
  };

  const handleShare = () => {
    // Combine selected friends and manually entered usernames
    const friendUsernames = selectedFriends;
    const manualUsernames = newUsernames
      .split(/[,\n]/)
      .map((u) => u.trim())
      .filter((u) => u.length > 0);

    const allUsernames = [...new Set([...friendUsernames, ...manualUsernames])];

    if (allUsernames.length === 0) {
      setError("Please select at least one friend or enter usernames");
      return;
    }

    onShare(allUsernames, permissionLevel);
    handleClearAll();
  };

  const handleClearAll = () => {
    setSelectedFriends([]);
    setNewUsernames("");
    setPermissionLevel("view");
    setError("");
  };

  const totalRecipients =
    selectedFriends.length +
    newUsernames.split(/[,\n]/).filter((u) => u.trim().length > 0).length;

  return (
    <>
      {/* Backdrop */}
      <div
        className={`share-backdrop ${isOpen ? "open" : ""}`}
        onClick={onClose}
      />

      {/* Panel */}
      <div className={`share-panel ${isOpen ? "open" : ""}`}>
        {/* Header */}
        <div className="share-header">
          <h2>Share Points</h2>
          <button
            className="share-close"
            onClick={onClose}
            aria-label="Close share panel"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="share-content">
          {/* Selected Points Info */}
          <div className="share-info">
            <p>
              <strong>{selectedPointIds.length}</strong> point
              {selectedPointIds.length !== 1 ? "s" : ""} selected
            </p>
          </div>

          {/* Permission Level Selector */}
          <div className="share-section">
            <h3>Permission Level</h3>
            <div className="permission-selector">
              <label className="permission-option">
                <input
                  type="radio"
                  name="permission"
                  value="view"
                  checked={permissionLevel === "view"}
                  onChange={() => setPermissionLevel("view")}
                />
                <div className="permission-details">
                  <strong>View</strong>
                  <span>Can view points and annotations</span>
                </div>
              </label>
              <label className="permission-option">
                <input
                  type="radio"
                  name="permission"
                  value="edit"
                  checked={permissionLevel === "edit"}
                  onChange={() => setPermissionLevel("edit")}
                />
                <div className="permission-details">
                  <strong>Edit</strong>
                  <span>Can view and edit points and annotations</span>
                </div>
              </label>
              <label className="permission-option">
                <input
                  type="radio"
                  name="permission"
                  value="manage"
                  checked={permissionLevel === "manage"}
                  onChange={() => setPermissionLevel("manage")}
                />
                <div className="permission-details">
                  <strong>Manage</strong>
                  <span>Can view, edit, and share with others</span>
                </div>
              </label>
            </div>
          </div>

          {/* Friends List */}
          <div className="share-section">
            <h3>Friends</h3>
            {isLoading ? (
              <div className="loading-message">Loading friends...</div>
            ) : friends.length === 0 ? (
              <div className="empty-message">
                No friends yet. Add friends from the Friends page or enter
                usernames below.
              </div>
            ) : (
              <div className="friends-list">
                {friends.map((friend) => (
                  <label key={friend.id} className="friend-option">
                    <input
                      type="checkbox"
                      checked={selectedFriends.includes(friend.username)}
                      onChange={() => handleToggleFriend(friend.username)}
                    />
                    <span className="friend-name">{friend.username}</span>
                    <span className="friend-stats">
                      {friend.shares_sent_count} shared
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* New Usernames */}
          <div className="share-section">
            <h3>Add New Users</h3>
            <p className="section-description">
              Enter usernames separated by commas or new lines
            </p>
            <textarea
              className="usernames-textarea"
              placeholder="username1, username2&#10;username3"
              value={newUsernames}
              onChange={(e) => setNewUsernames(e.target.value)}
              rows={4}
            />
          </div>

          {/* Error Message */}
          {error && <div className="error-message">{error}</div>}
        </div>

        {/* Footer */}
        <div className="share-footer">
          <button onClick={handleClearAll} className="btn-secondary">
            Clear All
          </button>
          <button
            onClick={handleShare}
            className="btn-primary"
            disabled={totalRecipients === 0}
          >
            Share with {totalRecipients || 0} user
            {totalRecipients !== 1 ? "s" : ""}
          </button>
        </div>
      </div>
    </>
  );
}
