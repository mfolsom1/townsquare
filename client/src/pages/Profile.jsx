import React, { useState } from "react";
import "./Profile.css";
import CreateEvent from "../components/CreateEvent.js"; 

const initialsFromName = (name = "User") =>
  name.trim().split(/\s+/).slice(0, 2).map(p => p[0]?.toUpperCase()).join("") || "U";

export default function ProfilePage({
  fullName    = "New User",
  username    = "user",
  friends     = 0,
  bio         = "",
  location    = "",
  study       = "",
  interests   = [],
  myEvents    = [],
  goingTo     = [],
  onCreateEvent,               // optional callback(newEvent)
}) {
  const initials = initialsFromName(fullName);
  const hasMyEvents = myEvents.length > 0;
  const hasGoingTo  = goingTo.length  > 0;

  // Control CreateEvent modal
  const [isCreateOpen, setCreateOpen] = useState(false);
  const openCreate = () => setCreateOpen(true);
  const closeCreate = () => setCreateOpen(false);

  const handleCreate = (data) => {
    // Bubble up to parent/app if provided
    if (typeof onCreateEvent === "function") onCreateEvent(data);
  };

  return (
    <main className="pf">
      <div className="pf-wrap">
        {/* LEFT */}
        <section className="pf-left">
          <div className="pf-user">
            <div className="pf-avatar"><span>{initials}</span></div>

            <div className="pf-user-block">
              <h1 className="pf-name">{fullName}</h1>
              <div className="pf-handle">@{username}</div>

              <div className="pf-row">
                <div className="pf-friends"><strong>{friends}</strong> Friends</div>
                <a className="pf-btn" href="/settings">Edit Profile</a>
              </div>

              {location && <div className="pf-sub">{location}</div>}
              {study    && <div className="pf-sub">{study}</div>}
              {bio      && <div className="pf-sub">{bio}</div>}
            </div>
          </div>

          <div className="pf-card pf-interests">
            <div className="pf-title">Interests</div>
            {interests.length ? (
              <div className="pf-pills">
                {interests.map((t, i) => <span key={i} className="pf-pill">{t}</span>)}
              </div>
            ) : (
              <div className="pf-empty">Interests from your profile.</div>
            )}
          </div>
        </section>

        {/* RIGHT */}
        <section className="pf-right">
          <div className="pf-card pf-list">
            <div className="pf-title">My Events</div>
            {hasMyEvents ? (
              <div className="pf-grid">
                {myEvents.map((e, i) => (
                  <div key={i} className="pf-event">
                    <div className="pf-thumb" />
                    <div>
                      <div className="pf-event-title">{e.title}</div>
                      <div className="pf-event-sub">{e.date} • {e.location}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="pf-empty">
                No events yet.{" "}
                <button type="button" className="pf-linkbtn" onClick={openCreate}>
                  Create one
                </button>.
              </div>
            )}
          </div>

          <div className="pf-card pf-list">
            <div className="pf-title">Going To</div>
            {hasGoingTo ? (
              <div className="pf-grid">
                {goingTo.map((e, i) => (
                  <div key={i} className="pf-event">
                    <div className="pf-thumb" />
                    <div>
                      <div className="pf-event-title">{e.title}</div>
                      <div className="pf-event-sub">{e.date} • {e.location}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="pf-empty">
                Nothing RSVP’d. <a href="/discover">Discover events</a>.
              </div>
            )}
          </div>
        </section>
      </div>

      {/* CreateEvent modal */}
      <CreateEvent open={isCreateOpen} onClose={closeCreate} onCreate={handleCreate} />
    </main>
  );
}
