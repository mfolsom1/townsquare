
// Modal for editing organization profile
// -------------------------------------------

import React, { useState, useEffect } from "react";
import "./OrgEditProfile.css";

export default function OrgEditProfile({ open, onClose, initial, onSave }) {
  // ADDED: local form state
  const [name, setName] = useState(initial?.name || "");
  const [email, setEmail] = useState(initial?.email || "");
  const [location, setLocation] = useState(initial?.location || "");
  const [about, setAbout] = useState(initial?.about || "");
  const [tagsText, setTagsText] = useState(
    Array.isArray(initial?.tags) ? initial.tags.join(", ") : ""
  );

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // ADDED: sync external updates into modal
  useEffect(() => {
    setName(initial?.name || "");
    setEmail(initial?.email || "");
    setLocation(initial?.location || "");
    setAbout(initial?.about || "");
    setTagsText(
      Array.isArray(initial?.tags) ? initial.tags.join(", ") : ""
    );
  }, [initial]);

  if (!open) return null;

  // ADDED: handle save
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);

    const tags = tagsText
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    const payload = { name, email, location, about, tags };

    try {
      await onSave(payload);
      setSaving(false);
      onClose();
    } catch (err) {
      setError(err?.message || "Failed to save changes");
      setSaving(false);
    }
  };

  return (
    <div className="org-modal-backdrop">
      <div className="org-modal">
        <div className="org-modal-header">
          <h2>Edit Organization Profile</h2>

          {/* ADDED: close button */}
          <button className="org-modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form className="org-modal-body" onSubmit={handleSubmit}>
          {/* ADDED: Name input */}
          <label className="org-field">
            <span className="org-field-label">Organization Name</span>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>

          {/* ADDED: Email input */}
          <label className="org-field">
            <span className="org-field-label">Email</span>
            <input value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>

          {/* ADDED: Location input */}
          <label className="org-field">
            <span className="org-field-label">Location</span>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </label>

          {/* ADDED: About field */}
          <label className="org-field">
            <span className="org-field-label">About</span>
            <textarea
              rows={4}
              value={about}
              onChange={(e) => setAbout(e.target.value)}
            />
          </label>

          {/* ADDED: Tags field */}
          <label className="org-field">
            <span className="org-field-label">Tags</span>
            <input
              value={tagsText}
              onChange={(e) => setTagsText(e.target.value)}
              placeholder="Arts, Music, Tech"
            />
          </label>

          {/* ADDED: error display */}
          {error && <div className="org-modal-error">{error}</div>}

          <div className="org-modal-footer">
            {/* ADDED: cancel button */}
            <button
              type="button"
              className="org-btn-secondary"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>

            {/* ADDED: save button */}
            <button type="submit" className="org-btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
