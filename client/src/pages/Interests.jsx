import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Interests.css";

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
  const nav = useNavigate();

  //TO DO: GET INTERESTS
  if(loading == true)
    setLoading(false);

  const toggleInterest = (id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    //TO DO: SAVE INTERESTS

    nav("/discover");
  };

  if (loading) return <p>Loading interests...</p>;

  return (
    <main className="interests-wrap">
      <form className="interests-card" onSubmit={handleSubmit}>
        <h1 className="interests-title">Choose Interests</h1>

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
