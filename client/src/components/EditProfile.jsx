import React, { useEffect, useRef, useState } from "react";
import "./EditProfile.css";

/**
 * Props:
 *  - open: boolean
 *  - onClose: () => void
 *  - initial: { fullName, username, bio, location }
 *  - onSave:  ({ fullName, username, bio, location }) => Promise<updatedValues>
 */
export default function EditProfile({ open, onClose, initial, onSave }) {
  const [fullName, setFullName] = useState(initial?.fullName || "");
  const [username, setUsername] = useState(initial?.username || "");
  const [bio, setBio]           = useState(initial?.bio || "");
  const [location, setLocation] = useState(initial?.location || "");
  const [error, setError]       = useState("");
  const [saving, setSaving]     = useState(false);

  const firstRef = useRef(null);

  // Sync fields when opened or when initial changes
  useEffect(() => {
    if (!open) return;
    setFullName(initial?.fullName || "");
    setUsername(initial?.username || "");
    setBio(initial?.bio || "");
    setLocation(initial?.location || "");
    setError("");
    setTimeout(() => firstRef.current?.focus(), 0);
  }, [open, initial]);

  // Close on overlay click
  const handleOverlay = (e) => {
    if (e.target.dataset.overlay === "true") onClose?.();
  };

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!fullName.trim()) return setError("Display name is required.");
    if (username && !/^[a-z0-9_]{3,30}$/i.test(username)) {
      return setError("Username must be 3–30 chars: letters, numbers, underscore.");
    }

    try {
      setSaving(true);
      await onSave?.({
        fullName: fullName.trim(),
        username: username.trim(),
        bio: bio.trim(),
        location: location.trim(),
      });
      onClose?.();
    } catch (err) {
      setError(err?.message || "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="epm-overlay"
      data-overlay="true"
      onMouseDown={handleOverlay}
      aria-hidden={false}
    >
      <div
        className="epm-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="epm-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <header className="epm-head">
          <h2 id="epm-title">Edit Profile</h2>
          <button className="epm-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <form className="epm-form" onSubmit={handleSubmit}>
          {error && <div className="epm-error">{error}</div>}

          <label className="epm-field">
            <span>Display Name</span>
            <input
              ref={firstRef}
              type="text"
              value={fullName}
              maxLength={60}
              placeholder="Your name"
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </label>

          <label className="epm-field">
            <span>Username</span>
            <div className="epm-username">
              <span className="epm-at">@</span>
              <input
                type="text"
                value={username}
                maxLength={30}
                placeholder="username"
                onChange={(e) => setUsername(e.target.value.replace(/\s/g, ""))}
              />
            </div>
            <small className="epm-help">Letters, numbers, underscore. No spaces.</small>
          </label>

          <label className="epm-field">
            <span>Location</span>
            <input
              type="text"
              value={location}
              maxLength={80}
              placeholder="City, State"
              onChange={(e) => setLocation(e.target.value)}
            />
          </label>

          <label className="epm-field">
            <span>Bio</span>
            <textarea
              value={bio}
              rows={4}
              maxLength={240}
              placeholder="Tell people a bit about you…"
              onChange={(e) => setBio(e.target.value)}
            />
            <small className="epm-help">{bio.length}/240 characters</small>
          </label>

          <div className="epm-actions">
            <button type="button" className="epm-btn secondary" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="epm-btn primary" disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
