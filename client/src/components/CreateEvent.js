import React, { useEffect, useState } from "react";
import "./CreateEvent.css";
import { useAuth } from "../auth/AuthContext";
import { createEvent } from "../api";

/* Event categories from the database */
const EVENT_CATEGORIES = [
  { id: 1, name: "Gator Sports", description: "Chomp chomp! Football, basketball, and all UF athletic events." },
  { id: 2, name: "UF Campus Life", description: "Events happening on the University of Florida campus." },
  { id: 3, name: "Local Music & Arts", description: "Concerts at local venues, art walks, and theater." },
  { id: 4, name: "Outdoor & Nature", description: "Explore Gainesville's beautiful parks, prairies, and springs." },
  { id: 5, name: "Food & Breweries", description: "From downtown food trucks to local craft breweries." },
  { id: 6, name: "Community & Markets", description: "Farmers markets, volunteer meetups, and local festivals." },
  { id: 7, name: "Tech & Innovation", description: "Meetups and workshops from Gainesville's growing tech scene." },
];

export default function CreateEvent({ open, onClose, onCreate }) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new FormData(e.currentTarget);
      const data = Object.fromEntries(formData);

      // Validate required fields
      if (!data.title || !data.startDateTime || !data.endDateTime || !data.location || !data.categoryId) {
        throw new Error("Please fill in all required fields");
      }

      // Validate that end time is after start time
      const startTime = new Date(data.startDateTime);
      const endTime = new Date(data.endDateTime);
      if (endTime <= startTime) {
        throw new Error("End time must be after start time");
      }

      // Get Firebase ID token for authentication
      const idToken = await user.getIdToken();

      // Prepare event data for the backend (using PascalCase as expected by the API)
      const eventData = {
        Title: data.title.trim(),
        Description: data.description?.trim() || null,
        StartTime: startTime.toISOString(),
        EndTime: endTime.toISOString(),
        Location: data.location.trim(),
        CategoryID: parseInt(data.categoryId),
        MaxAttendees: data.maxAttendees ? parseInt(data.maxAttendees) : null,
        ImageURL: data.imageUrl?.trim() || null,
      };

      // Call the backend API
      const response = await createEvent(idToken, eventData);

      // Call the parent component's onCreate callback if provided
      onCreate?.(response.new_event);

      // Close the modal on success
      onClose();
    } catch (err) {
      setError(err.message || "Failed to create event");
    } finally {
      setLoading(false);
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
          {error && <div className="cem-error">{error}</div>}
          
          <label>
            Title *
            <input 
              name="title" 
              placeholder="e.g., UF Hackathon" 
              maxLength="200"
              required 
            />
          </label>

          <label>
            Category *
            <select name="categoryId" required>
              <option value="">Select a category</option>
              {EVENT_CATEGORIES.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>

          <div className="cem-date-time-grid">
            <label>
              Start Date & Time *
              <input 
                type="datetime-local" 
                name="startDateTime" 
                min={new Date().toISOString().slice(0, 16)}
                required 
              />
            </label>

            <label>
              End Date & Time *
              <input 
                type="datetime-local" 
                name="endDateTime" 
                min={new Date().toISOString().slice(0, 16)}
                required 
              />
            </label>
          </div>

          <label>
            Location *
            <input 
              name="location" 
              placeholder="e.g., Ben Hill Griffin Stadium, Gainesville, FL" 
              maxLength="300"
              required 
            />
          </label>

          <label>
            Description
            <textarea 
              name="description" 
              rows="4" 
              placeholder="Tell people what your event is about..."
              maxLength="1000"
            />
          </label>

          <div className="cem-optional-grid">
            <label>
              Max Attendees
              <input 
                type="number" 
                name="maxAttendees" 
                placeholder="e.g., 50"
                min="1"
                max="10000"
              />
            </label>

            <label>
              Image URL
              <input 
                type="url" 
                name="imageUrl" 
                placeholder="https://example.com/image.jpg"
                maxLength="500"
              />
            </label>
          </div>

          <footer className="cem-actions">
            <button type="button" onClick={onClose} className="cem-btn ghost" disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="cem-btn primary" disabled={loading}>
              {loading ? "Creating..." : "Create Event"}
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}
