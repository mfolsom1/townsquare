import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Interests.css";
import { useAuth } from "../auth/AuthContext";
import { getUserInterests, setUserInterests, getUserProfile, updateUserProfile } from "../api";

const interestsList = [
  { id: "education", label: "Education", icon: "/images/education.png" },
  { id: "music", label: "Music", icon: "/images/music.png" },
  { id: "sports", label: "Sports", icon: "/images/sports.png" },
  { id: "food", label: "Food", icon: "/images/food.png" },
  { id: "community", label: "Community", icon: "/images/community.png" },
  { id: "tech", label: "Tech", icon: "/images/tech.png" },
  { id: "entertainment", label: "Fun", icon: "/images/fun.png" },
  { id: "outdoors", label: "Outdoors", icon: "/images/outdoors.png" },
  { id: "arts", label: "Arts", icon: "/images/arts.png" },
  { id: "career", label: "Career", icon: "/images/career.png" },
];

export default function Interests() {
  const [selected, setSelected] = useState([]);
  const [bio, setBio] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const nav = useNavigate();
  const { user, isNewUser, setIsNewUser } = useAuth();

  // Load user's existing interests and bio when component mounts
  useEffect(() => {
    let mounted = true;
    async function loadUserData() {
      if (!user) {
        setLoading(false);
        return;
      }
      try {
        const idToken = await user.getIdToken();
        
        // Load user profile (includes bio)
        const profileRes = await getUserProfile(idToken);
        if (mounted) {
          setBio(profileRes?.user?.bio || "");
        }
        
        // Load interests
        const interestsRes = await getUserInterests(idToken);
        const interests = interestsRes?.interests || [];
        if (!mounted) return;
        // Normalize: our local ids use lowercase keys; backend likely stores names
        setSelected(interests.map((i) => String(i).toLowerCase()));
      } catch (err) {
        console.error("Failed to load user data", err);
        if (mounted) setError(err.message || "Failed to load user data");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadUserData();
    return () => (mounted = false);
  }, [user]);

  const toggleInterest = (id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!user) {
      setError("You must be signed in to save your profile");
      return;
    }

    try {
      setLoading(true);
      const idToken = await user.getIdToken();
      
      // Convert selected ids back to interest names expected by backend
      const selectedNames = interestsList
        .filter((i) => selected.includes(i.id))
        .map((i) => i.label);

      // Save both interests and bio
      await setUserInterests(idToken, selectedNames);
      
      // Update bio if it has content
      if (bio.trim()) {
        await updateUserProfile(idToken, { bio: bio.trim() });
      }
      
      // Clear the new user state since profile is now set
      if (isNewUser) {
        setIsNewUser(false);
      }
      
      nav("/discover");
    } catch (err) {
      console.error("Failed to save profile", err);
      setError(err.message || "Failed to save profile");
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    setError(null);
    if (!user) {
      setError("You must be signed in to continue");
      return;
    }

    try {
      setLoading(true);
      const idToken = await user.getIdToken();
      
      // Set empty interests array to indicate user has "completed" this step
      await setUserInterests(idToken, []);
      
      // Clear the new user state since they've chosen to skip
      if (isNewUser) {
        setIsNewUser(false);
      }
      
      nav("/discover");
    } catch (err) {
      console.error("Failed to skip interests setup", err);
      setError(err.message || "Failed to continue");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p>Loading interests...</p>;

  return (
    <main className="interests-wrap">
      <form className="interests-card" onSubmit={handleSubmit}>
        <h1 className="interests-title">Set Up Your Profile</h1>

        {error && <div className="error">{error}</div>}

        <h2 className="interests-subtitle">Choose Your Interests</h2>
        <div className="interests-menu">
          {interestsList.map((i) => (
            <div key={i.id} className="interest-item">
              <button
                type="button"
                className={`interest-circle ${
                  selected.includes(i.id) ? "selected" : ""
                }`}
                onClick={() => toggleInterest(i.id)}
              >
                <img src={i.icon} alt={i.label} className="interest-icon" />
              </button>
              <div className="interest-label">{i.label}</div>
            </div>
          ))}
        </div>

        <div className="bio-section">
          <h2 className="bio-title">Write Your Bio</h2>
          <textarea
            className="bio-textarea"
            placeholder="Tell others about yourself... What are your hobbies? What do you do for work? What makes you unique?"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            maxLength={500}
            rows={4}
          />
          <div className="bio-counter">
            {bio.length}/500 characters
          </div>
        </div>

        <div className="interests-buttons">
          <button
            type="submit"
            className="auth-btn primary"
            disabled={selected.length === 0 && bio.trim().length === 0}
          >
            Save & Continue
          </button>
          <button
            type="button"
            className="auth-btn secondary"
            onClick={handleSkip}
            disabled={loading}
          >
            Skip for now
          </button>
        </div>
      </form>
    </main>
  );
}
