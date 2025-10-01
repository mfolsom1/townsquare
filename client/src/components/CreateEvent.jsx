import React, { useEffect } from "react";
import "./CreateEvent.css";
import { createEvent } from "../services/eventsApi";

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    const form = Object.fromEntries(new FormData(e.currentTarget));
    const startAt =
      form.datetime ? new Date(form.datetime).toISOString() : null;

      try {
      const created = await createEvent({
        title: form.title,
        desc: form.description || "",
        location: form.location || "",
        startAt,                    // ISO string
        // optional fields 
        category: form.category || "",
        coverUrl: form.coverUrl || null,
      });
      
      onCreate?.(created);          // keep your callback if someone uses it
      onClose();
    } catch (err) {
      console.error(err);
      alert("Could not create event. Please try again.");
    }
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
