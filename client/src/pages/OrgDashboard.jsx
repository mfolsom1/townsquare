import React, { useState } from "react";
import "./OrgDashboard.css";
import CreateEvent from "../components/CreateEvent";

import OrgEditProfile from "../components/OrgEditProfile";

const initialsFromName = (name = "Organization") =>
  name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("") || "O";

export default function OrgDashboard({
  events = [],
  onCreateEvent,
  onSaveOrgProfile,
  initialOrg,
}) {

    const mockAnalytics = [
    { label: "10/15", value: 80 },
    { label: "10/22", value: 120 },
    { label: "10/28", value: 70 },
    { label: "10/31", value: 150 },
  ];

// fallback if container doesn't pass an org yet
const fallbackOrg = {
  name: "Umbrella Corp",
  handle: "@umbrella",
  location: "Gainesville, FL",
  email: "email@example.com",
  followers: 8,
  bannerUrl:
    "https://www.google.com/url?sa=i&url=https%3A%2F%2Fdesignbundles.net%2Fladadikart%2F2893326-umbrellas-in-hands-banner-rainy-day-storm-and-hand&psig=AOvVaw07DHeE7a-r6GSWYf3Mo78O&ust=1763036993946000&source=images&cd=vfe&opi=89978449&ved=0CBYQjRxqFwoTCNDxv-XO7JADFQAAAAAdAAAAABAE=format&fit=crop",
  avatarUrl: null,
  about: "Welcome to Umbrella Corporations.",
  tags: ["Arts", "Music", "Tech", "Food & Drink"],
};

// org state is seeded from container
const [org, setOrg] = useState(initialOrg || fallbackOrg);



  const initials = initialsFromName(org.name);

      // Create Event Modal 
        const [isCreateOpen, setCreateOpen] = useState(false);
      const openCreate = () => setCreateOpen(true);
      const closeCreate = () => setCreateOpen(false);

      const handleCreate = (data) => {
        if (typeof onCreateEvent === "function") {
          onCreateEvent(data);
        }
        console.log("New event created:", data);
      };
      // Edit Profile Modal
        const [isEditOpen, setEditOpen] = useState(false);
      const openEdit = () => setEditOpen(true);
      const closeEdit = () => setEditOpen(false);

      const handleSaveProfile = async (payload) => {
        // payload: { name, email, location, about, tags }
        // ALWAYS update the UI immediately from the form values
        setOrg((prev) => ({
          ...prev,
          name: payload.name ?? prev.name,
          email: payload.email ?? prev.email,
          location: payload.location ?? prev.location,
          about: payload.about ?? prev.about,
          tags: Array.isArray(payload.tags) ? payload.tags : prev.tags,
        }));

        // \persist to backend (container)
        try {
          if (typeof onSaveOrgProfile === "function") {
            await onSaveOrgProfile(payload);
          }
        } catch (e) {
          console.error("Failed to save organization profile:", e);
          // (optional) you could show a toast or revert state here
        }

        return payload;
      };

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

            <button className="org-edit-btn" type="button" onClick={openEdit}>
              Edit Profile
            </button>

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

        {/* RIGHT COLUMN */}
        <main className="org-main">
          {/* EVENTS CARD */}
          <div className="org-card org-events">
            <div className="org-events-header">
              <div className="org-events-title">Events</div>
            </div>

            {/* EVENTS GRID */}
            {events.length ? (
              <div className="org-events-grid">
                {events.map((e) => (
                  <div key={e.id} className="org-event">
                    <div className="org-event-thumb">
                      {e.imageUrl ? (
                        <img src={e.imageUrl} alt={e.title} />
                      ) : (
                        <div className="org-event-thumb-placeholder">
                          <span className="material-symbols-outlined">
                            event
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="org-event-body">
                      <div className="org-event-title">{e.title}</div>
                      <div className="org-event-sub">
                        {e.date} • {e.location}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="org-events-empty">No events yet.</div>
            )}
          </div>

          {/* CREATE EVENT BUTTON */}
          <div className="org-events-footer">
            <button
              className="org-events-cta"
              type="button"
              onClick={openCreate}
            >
              Create Event
            </button>
          </div>

          {/* ANALYTICS CARD (MOCK) */}
          <section className="org-card org-analytics">
            <div className="org-analytics-header">
              <div>
                <div className="org-analytics-title">Analytics</div>
                <div className="org-analytics-sub">Last 30 days</div>
              </div>
            </div>

            <div className="org-analytics-tabs">
              <button className="org-analytics-tab org-analytics-tab--active">
                Attendees
              </button>
              <button className="org-analytics-tab">RSVP’s</button>
              <button className="org-analytics-tab">Events</button>
              <button className="org-analytics-tab">New Followers</button>
            </div>

            <div className="org-analytics-chart">
              <div className="org-analytics-ylabel">Attendees</div>
              <div className="org-analytics-bars">
                {mockAnalytics.map((pt) => (
                  <div key={pt.label} className="org-analytics-bar-group">
                    <div
                      className="org-analytics-bar"
                      style={{ height: `${pt.value}px` }}
                    />
                    <div className="org-analytics-xlabel">{pt.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </main>
      </div>

      
 {/* ADDED — Create Event Modal */}
      <CreateEvent
        open={isCreateOpen}
        onClose={closeCreate}
        onCreate={handleCreate}
      />

      {/* ADDED — Edit Profile Modal */}
      <OrgEditProfile
        open={isEditOpen}
        onClose={closeEdit}
        initial={{
          name: org.name,
          email: org.email,
          location: org.location,
          about: org.about,
          tags: org.tags,
        }}
        onSave={handleSaveProfile}
      />
    </div>
  );
}