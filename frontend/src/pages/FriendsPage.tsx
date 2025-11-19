/**
 * Friends List Page
 *
 * Displays all friends with share statistics and management options.
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getFriends, addFriend, type Friend } from "../api/friends";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import "./FriendsPage.css";

export function FriendsPage() {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [isAddingFriend, setIsAddingFriend] = useState(false);
  const [newFriendUsername, setNewFriendUsername] = useState("");
  const [addFriendError, setAddFriendError] = useState("");
  const navigate = useNavigate();

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

  useEffect(() => {
    loadFriends();
  }, []);

  const handleAddFriend = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newFriendUsername.trim()) {
      setAddFriendError("Username is required");
      return;
    }

    setIsAddingFriend(true);
    setAddFriendError("");

    try {
      await addFriend(newFriendUsername.trim());
      setNewFriendUsername("");
      await loadFriends(); // Reload friends list
    } catch (err) {
      setAddFriendError(getErrorMessage(err));
    } finally {
      setIsAddingFriend(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message="Loading friends..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error loading friends</h2>
        <p>{error}</p>
        <button onClick={loadFriends} className="btn-primary">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="friends-page">
      <div className="friends-header">
        <h1>Friends</h1>
        <p className="friends-subtitle">
          Manage your friends and shared points
        </p>
      </div>

      {/* Add Friend Form */}
      <div className="add-friend-section">
        <h2>Add Friend</h2>
        <form onSubmit={handleAddFriend} className="add-friend-form">
          <input
            type="text"
            className="friend-username-input"
            placeholder="Enter username..."
            value={newFriendUsername}
            onChange={(e) => setNewFriendUsername(e.target.value)}
            disabled={isAddingFriend}
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={isAddingFriend}
          >
            {isAddingFriend ? "Adding..." : "Add Friend"}
          </button>
        </form>
        {addFriendError && (
          <div className="error-message">{addFriendError}</div>
        )}
      </div>

      {/* Friends List */}
      <div className="friends-list-section">
        <h2>
          Your Friends ({friends.length})
        </h2>

        {friends.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">👥</div>
            <h3>No friends yet</h3>
            <p>
              Add friends by entering their username above to start sharing
              points.
            </p>
          </div>
        ) : (
          <div className="friends-grid">
            {friends.map((friend) => (
              <div
                key={friend.id}
                className="friend-card"
                onClick={() => navigate(`/friends/${friend.friendship_id}`)}
              >
                <div className="friend-card-header">
                  <div className="friend-avatar">
                    {friend.username.charAt(0).toUpperCase()}
                  </div>
                  <div className="friend-info">
                    <h3 className="friend-username">{friend.username}</h3>
                    <p className="friend-date">
                      Friends since {formatDate(friend.friendship_created_at)}
                    </p>
                  </div>
                </div>

                <div className="friend-stats">
                  <div className="friend-stat">
                    <span className="stat-value">
                      {friend.shares_sent_count}
                    </span>
                    <span className="stat-label">Shared with them</span>
                  </div>
                  <div className="friend-stat">
                    <span className="stat-value">
                      {friend.shares_received_count}
                    </span>
                    <span className="stat-label">Received from them</span>
                  </div>
                </div>

                <div className="friend-card-footer">
                  <span className="view-details-link">
                    View details →
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
