import React, { useState, useEffect } from "react";
import { followUser, unfollowUser, checkFollowingStatus } from "../api";
import { useAuth } from "../auth/AuthContext";
import "./FollowButton.css";

const FollowButton = ({ targetUid, targetUsername, className = "" }) => {
  const { user } = useAuth();
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkStatus = async () => {
      if (!user || !targetUid || targetUid === user.uid) {
        setLoading(false);
        return;
      }

      try {
        const idToken = await user.getIdToken();
        const response = await checkFollowingStatus(idToken, targetUid);
        setIsFollowing(response.is_following);
      } catch (err) {
        console.warn("Failed to check following status:", err);
        setError("Failed to load following status");
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
  }, [user, targetUid]);

  const handleFollowToggle = async () => {
    if (!user) {
      setError("Please log in to follow users");
      return;
    }

    if (!targetUid) {
      setError("Invalid user");
      return;
    }

    setError(null);
    setActionLoading(true);

    // Optimistic update
    const previousState = isFollowing;
    setIsFollowing(!isFollowing);

    try {
      const idToken = await user.getIdToken();
      
      if (isFollowing) {
        await unfollowUser(idToken, targetUid, targetUsername);
      } else {
        await followUser(idToken, targetUid, targetUsername);
      }
    } catch (err) {
      // Rollback optimistic update
      setIsFollowing(previousState);
      setError(err.message || "Failed to update follow status");
    } finally {
      setActionLoading(false);
    }
  };

  // Don't show button if user is not logged in, or if it's the user's own profile
  if (!user || !targetUid || targetUid === user.uid) {
    return null;
  }

  if (loading) {
    return <div className={`follow-button loading ${className}`}>Loading...</div>;
  }

  return (
    <div className="follow-button-container">
      <button
        className={`follow-button ${isFollowing ? "following" : "not-following"} ${className}`}
        onClick={handleFollowToggle}
        disabled={actionLoading}
      >
        {actionLoading ? "..." : isFollowing ? "Unfollow" : "Follow"}
      </button>
      {error && <div className="follow-error">{error}</div>}
    </div>
  );
};

export default FollowButton;