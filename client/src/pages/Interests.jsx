import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Interests.css";
import { useAuth } from "../auth/AuthContext";
import { getUserInterests, setUserInterests } from "../api";

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const nav = useNavigate();
  const { user } = useAuth();

  // Load user's existing interests when component mounts
  useEffect(() => {
    let mounted = true;
    async function loadInterests() {
      if (!user) {
        setLoading(false);
        return;
      }
      try {
        const idToken = await user.getIdToken();
        const res = await getUserInterests(idToken);
        // api returns object { success: true, interests: [...] }
        const interests = res?.interests || [];
        if (!mounted) return;
        // Normalize: our local ids use lowercase keys; backend likely stores names
        setSelected(interests.map((i) => String(i).toLowerCase()));
      } catch (err) {
        console.error("Failed to load user interests", err);
        if (mounted) setError(err.message || "Failed to load interests");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadInterests();
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
      setError("You must be signed in to save interests");
      return;
    }

    try {
      setLoading(true);
      const idToken = await user.getIdToken();
      // Convert selected ids back to interest names expected by backend
      // Here we assume backend expects capitalized/simple names; use labels from interestsList
      const selectedNames = interestsList
        .filter((i) => selected.includes(i.id))
        .map((i) => i.label);

      await setUserInterests(idToken, selectedNames);
      nav("/discover");
    } catch (err) {
      console.error("Failed to save interests", err);
      setError(err.message || "Failed to save interests");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p>Loading interests...</p>;

  return (
    <main className="interests-wrap">
      <form className="interests-card" onSubmit={handleSubmit}>
        <h1 className="interests-title">Choose Interests</h1>

        {error && <div className="error">{error}</div>}

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

        <button
          type="submit"
          className="auth-btn primary"
          disabled={selected.length === 0}
        >
          Continue
        </button>
      </form>
    </main>
  );
}
