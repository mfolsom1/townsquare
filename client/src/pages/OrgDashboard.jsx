import React from "react";
import "./OrgDashboard.css";


const initialsFromName = (name = "Organization") =>
  name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("") || "O";

export default function OrgDashboard() {
  // TODO: replace with real data from API
  const org = {
    name: "Umbrella Corp",
    handle: "@umbrella",
    location: "Gainesville, FL",
    email: "email@example.com",
    followers: 8,

    bannerUrl:
      "https://www.google.com/url?sa=i&url=https%3A%2F%2Fdesignbundles.net%2Fladadikart%2F2893326-umbrellas-in-hands-banner-rainy-day-storm-and-hand&psig=AOvVaw07DHeE7a-r6GSWYf3Mo78O&ust=1763036993946000&source=images&cd=vfe&opi=89978449&ved=0CBYQjRxqFwoTCNDxv-XO7JADFQAAAAAdAAAAABAE=format&fit=crop",
    // avatarUrl: null means we’ll show initials
    avatarUrl: null,
    about: "Welcome to Umbrella Corporations.",
    tags: ["Arts", "Music", "Tech", "Food & Drink"],
  };

  const initials = initialsFromName(org.name);

  return (
    <div className="org-page">
        {/*TODO: add picture insertion */}
      {/* Banner */}
      <div className="org-hero">
        <img className="org-banner" src={org.bannerUrl} alt="Organization banner" />

        {/* Avatar: show image if provided, else initials placeholder */}
        {org.avatarUrl ? (
          <img className="org-avatar" src={org.avatarUrl} alt={`${org.name} logo`} />
        ) : (
          <div className="org-avatar org-avatar-initials" aria-label={`${org.name} initials`}>
            <span>{initials}</span>
          </div>
        )}
      </div>

      {/* Left info section (unchanged) */}
      <div className="org-content">
        <aside className="org-sidebar">
          <div className="org-card">
            <div className="org-identity">
              <div className="org-name">{org.name}</div>
              <div className="org-handle">{org.handle}</div>
            </div>

            <div className="org-meta">
              <div className="org-meta-row">
                <span className="material-symbols-outlined">location_on</span>
                <span>{org.location}</span>
              </div>
              <div className="org-meta-row">
                <span className="material-symbols-outlined">mail</span>
                <a href={`mailto:${org.email}`}>{org.email}</a>
              </div>
              <div className="org-meta-row">
                <span className="material-symbols-outlined">group</span>
                <span>
                  <strong>{org.followers}</strong> Followers
                </span>
              </div>
            </div>

            <button className="org-edit-btn" type="button">Edit Profile</button>

            <div className="org-section">
              <div className="org-section-title">About</div>
              <p className="org-about">{org.about}</p>
            </div>

            <div className="org-section">
              <div className="org-section-title">Tags</div>
              <div className="org-tags">
                {org.tags.map((t) => (
                  <span className="org-tag" key={t}>{t}</span>
                ))}
              </div>
            </div>

            <button className="org-logout-btn" type="button">Logout</button>
          </div>
        </aside>

        {/* Right column placeholder (Events & Analytics) */}
        <main className="org-main">
          <div className="org-placeholder">
            Right column coming soon: Events & Analytics
          </div>
        </main>
      </div>
    </div>
  );
}
