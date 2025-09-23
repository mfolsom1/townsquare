import React, { useEffect } from "react";
import "./CreateEvent.css";
/* Placeholder until finalized format for create event */
/* popup modal */
export default function CreateEvent({ open, onClose, onCreate }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    onCreate?.(data); // TODO: send to backend later
    onClose();
  };

  return (
    /* close pop up */
    <div className="cem-backdrop" onClick={onClose}>
      <div className="cem-modal" onClick={(e) => e.stopPropagation()}>
        <header className="cem-header">
          <h3>Create Event</h3>
          <button className="cem-close" onClick={onClose} aria-label="Close">×</button>
        </header>

        <form className="cem-form" onSubmit={handleSubmit}>
          <label>
            Title
            <input name="title" placeholder="e.g., UF Hackathon" required />
          </label>

          <label>
            Date & Time
            <input type="datetime-local" name="datetime" required />
          </label>

          <label>
            Location
            <input name="location" placeholder="City, Venue" required />
          </label>

          <label>
            Description
            <textarea name="description" rows="4" placeholder="Details..." />
          </label>

          <footer className="cem-actions">
            <button type="button" onClick={onClose} className="cem-btn ghost">Cancel</button>
            <button type="submit" className="cem-btn primary">Create</button>
          </footer>
        </form>
      </div>
    </div>
  );
}
