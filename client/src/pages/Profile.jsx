import React, { useEffect, useState } from "react";
import "./Profile.css";
import CreateEvent from "../components/CreateEvent.js"; 
import EditProfile from "../components/EditProfile.jsx";
import { useAuth } from "../auth/AuthContext.jsx";
import { Link, useNavigate } from "react-router-dom";

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
  onSaveProfile
}) {
  
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const handleLogout = async () => {
    await logout();
    nav("/login", { replace: true })
  }

  // keep local snapshot so UI reflects edits immediately
  const [nameLocal, setNameLocal]         = useState(fullName);
  const [usernameLocal, setUsernameLocal] = useState(username);
  const [bioLocal, setBioLocal]           = useState(bio);
  const [locLocal, setLocLocal]           = useState(location);
  const initials = initialsFromName(nameLocal);

    // sync local state if container props change (e.g., after refetch)
    useEffect(() => {
    setNameLocal(fullName);
    setUsernameLocal(username);
    setBioLocal(bio);
    setLocLocal(location);
  }, [fullName, username, bio, location]);

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

  // Control EditProfile modal
  const [isEditOpen, setEditOpen] = useState(false);
  const openEdit = () => setEditOpen(true);
  const closeEdit = () => setEditOpen(false);

  // Save handler injected into modal; call backend if provided
  const handleSaveProfile = async (payload) => {
    // If parent gave a saver, call it; it can throw to display errors in modal
    const updated = typeof onSaveProfile === "function"
      ? await onSaveProfile(payload)
      : payload;
    // Use returned values (or payload) to update UI
    setNameLocal(updated.fullName ?? payload.fullName);
    setUsernameLocal(updated.username ?? payload.username);
    setBioLocal(updated.bio ?? payload.bio);
    setLocLocal(updated.location ?? payload.location);
    return updated; // modal will close on success
  };

  return (
    <main className="pf">
      <div className="pf-wrap">
        {/* LEFT */}
        <section className="pf-left">
          <div className="pf-user">
            <div className="pf-avatar"><span>{initials}</span></div>

            <div className="pf-user-block">
              <h1 className="pf-name">{nameLocal}</h1>
              <div className="pf-handle">@{usernameLocal}</div>


              {/*Location Display */}
               {locLocal && (
                 <div className="pf-sub pf-location pf-location-after">
                  <span className="material-symbols-outlined" aria-hidden="true">location_on</span>
                  <span>{locLocal}</span>
                </div>
              )}
              <div className="pf-row">
                <span className="pf-friends material-symbols-outlined">group</span>
                <div className="pf-friends"><strong>{friends}</strong> Friends</div>
              </div>
              {study    && <div className="pf-sub">{study}</div>}
              {bioLocal && <div className="pf-sub pf-bio">{bioLocal}</div>}
            </div>
            <button type="button" className="pf-btn" onClick={openEdit}>
              Edit Profile
            </button>
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
          <button className="org-logout-btn" type="button" onClick={handleLogout}>
              Logout
          </button>

        </section>

        {/* RIGHT */}
        <section className="pf-right">
          <div className="pf-card pf-list">
            <div className="pf-title">My Events</div>
            {hasMyEvents ? (
              <div className="pf-grid">
                {myEvents.map((e, i) => (
                  <div key={i} className="pf-event">
                    <div className="pf-thumb">
                      {e.imageUrl ? (
                        <img src={e.imageUrl} alt={e.title} />
                      ) : (
                        <div className="pf-thumb-placeholder">
                          <span className="material-symbols-outlined">event</span>
                        </div>
                      )}
                    </div>
                    <div className="pf-event-body">
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
                    <div className="pf-thumb">
                      {e.imageUrl ? (
                        <img src={e.imageUrl} alt={e.title} />
                      ) : (
                        <div className="pf-thumb-placeholder">
                          <span className="material-symbols-outlined">event</span>
                        </div>
                      )}
                    </div>
                    <div className="pf-event-body">
                      <div className="pf-event-title">{e.title}</div>
                      <div className="pf-event-sub">{e.date} • {e.location}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="pf-empty">
                Nothing RSVP’d. <a className="pf-linkbtn" href="/discover">Discover events</a>.
              </div>
            )}
          </div>
        </section>
      </div>

      {/* CreateEvent modal */}
      <CreateEvent open={isCreateOpen} onClose={closeCreate} onCreate={handleCreate} />

      {/* EditProfile modal */}
      <EditProfile
        open={isEditOpen}
        onClose={closeEdit}
        initial={{
          fullName: nameLocal,
          username: usernameLocal,
          bio: bioLocal,
          location: locLocal,
        }}
        onSave={handleSaveProfile}
      />
    </main>
  );
}
