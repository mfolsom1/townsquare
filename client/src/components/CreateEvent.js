import React, { useEffect, useState, useMemo } from "react";
import "./CreateEvent.css";
import { useAuth } from "../auth/AuthContext";
import { createEvent, getUserProfile } from "../api";

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
  const [userProfile, setUserProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);

  // Compute the minimum datetime value once per render
  const minDateTime = useMemo(() => new Date().toISOString().slice(0, 16), []);

  // Check if user is an organization account
  const isOrganization = userProfile?.user_type === 'organization';

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // When modal opens, fetch the user profile to check user_type
  useEffect(() => {
    let cancelled = false;
    async function loadUserProfile() {
      if (!open || !user) return;
      try {
        setLoadingProfile(true);
        setError("");
        const idToken = await user.getIdToken();
        const response = await getUserProfile(idToken);
        if (!cancelled) {
          setUserProfile(response?.user || null);
        }
      } catch (e) {
        if (!cancelled) {
          setError("Failed to load user profile. Please try again.");
          setUserProfile(null);
        }
      } finally {
        if (!cancelled) setLoadingProfile(false);
      }
    }
    loadUserProfile();
    return () => { cancelled = true; };
  }, [open, user]);

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prevent submission if not an organization account
    if (!isOrganization) {
      setError("You must be a verified organization to create events");
      return;
    }

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
      const msg = err?.message || "Failed to create event";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="cem-backdrop" onClick={onClose}>
      <div className="cem-modal" onClick={(e) => e.stopPropagation()}>
        <header className="cem-header">
          <h3>Create Event</h3>
          <button className="cem-close" onClick={onClose} aria-label="Close">×</button>
        </header>
        {loadingProfile ? (
          <div className="cem-form" style={{ padding: 16 }}>
            <div>Loading...</div>
          </div>
        ) : (
          <form className="cem-form" onSubmit={handleSubmit}>
            {error && <div className="cem-error">{error}</div>}

            {!isOrganization && (
              <div className="cem-warning" style={{
                backgroundColor: '#fff3cd',
                border: '1px solid #ffc107',
                borderRadius: '4px',
                padding: '12px',
                marginBottom: '16px',
                color: '#856404'
              }}>
                ⚠️ You must be a verified organization to create events
              </div>
            )}

            <label>
              Title *
              <input
                name="title"
                placeholder="e.g., UF Hackathon"
                maxLength="200"
                required
                disabled={!isOrganization}
              />
            </label>

            <label>
              Category *
              <select name="categoryId" required disabled={!isOrganization}>
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
                  min={minDateTime}
                  required
                  disabled={!isOrganization}
                />
              </label>

              <label>
                End Date & Time *
                <input
                  type="datetime-local"
                  name="endDateTime"
                  min={minDateTime}
                  required
                  disabled={!isOrganization}
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
                disabled={!isOrganization}
              />
            </label>

            <label>
              Description
              <textarea
                name="description"
                rows="4"
                placeholder="Tell people what your event is about..."
                maxLength="1000"
                disabled={!isOrganization}
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
                  disabled={!isOrganization}
                />
              </label>

              <label>
                Image URL
                <input
                  type="url"
                  name="imageUrl"
                  placeholder="https://example.com/image.jpg"
                  maxLength="500"
                  disabled={!isOrganization}
                />
              </label>
            </div>

            <footer className="cem-actions">
              <button type="button" onClick={onClose} className="cem-btn ghost" disabled={loading}>
                Cancel
              </button>
              <button
                type="submit"
                className="cem-btn primary"
                disabled={loading || !isOrganization}
                title={!isOrganization ? "You must be a verified organization to create events" : ""}
                style={{
                  cursor: !isOrganization ? 'not-allowed' : 'pointer',
                  opacity: !isOrganization ? 0.6 : 1
                }}
              >
                {loading ? "Creating..." : "Create Event"}
              </button>
            </footer>
          </form>
        )}
      </div>
    </div>
  );
}
