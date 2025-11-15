import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  getEventById,
  createOrUpdateRsvp,
  deleteRsvp,
  getUserRsvps,
  getUserPublicInfo,
} from "../api";
import { useAuth } from "../auth/AuthContext";
import RsvpModal from "../components/RsvpModal";
import FollowButton from "../components/FollowButton";
import "./EventDetail.css";

/* Re-using the same category details from the Discover page for consistency */
const categoryDetails = {
  1: { name: "Gator Sports", color: "#FA4616" },
  2: { name: "UF Campus Life", color: "#0021A5" },
  3: { name: "Local Music & Arts", color: "#FFC300" },
  4: { name: "Outdoor & Nature", color: "#1A9956" },
  5: { name: "Food & Breweries", color: "#900C3F" },
  6: { name: "Community & Markets", color: "#581845" },
  7: { name: "Tech & Innovation", color: "#2A6E99" },
  default: { name: "General", color: "#6C757D" },
};

const formatEventTimeRange = (startStr, endStr) => {
  const startDate = new Date(startStr);
  const endDate = new Date(endStr);
  const options = {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  };
  const startFormatted = startDate.toLocaleDateString("en-US", options);
  const endFormatted = endDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${startFormatted} to ${endFormatted}`;
};

export default function EventDetail() {
  const { eventId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [event, setEvent] = useState(null);
  const [organizer, setOrganizer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [rsvpStatus, setRsvpStatus] = useState(null);
  const [rsvpLoading, setRsvpLoading] = useState(false);
  const [rsvpError, setRsvpError] = useState(null);
  const [isRsvpOpen, setIsRsvpOpen] = useState(false);

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        const response = await getEventById(eventId);
        const eventData = response.event;
        setEvent(eventData);

        // Fetch organizer info
        if (eventData.organizer_uid) {
          try {
            const organizerResponse = await getUserPublicInfo(eventData.organizer_uid);
            setOrganizer(organizerResponse.user);
          } catch (err) {
            console.warn("Failed to fetch organizer info:", err);
          }
        }
      } catch (err) {
        setError(err.message || "Failed to load event details.");
      } finally {
        setLoading(false);
      }
    };

    fetchEvent();
  }, [eventId]); // Re-run the effect if the eventId changes

  // Effect: load current user's RSVP for this event (if logged in)
  useEffect(() => {
    let mounted = true;
    const loadMyRsvp = async () => {
      if (!user) {
        // If you want to require login, redirect like ProfileContainer:
        // navigate('/login', { replace: true }); return;
        return;
      }
      try {
        const idToken = await user.getIdToken();
        const resp = await getUserRsvps(idToken);
        const rsvps = resp?.rsvps || [];
        const mine = rsvps.find((r) => String(r.event_id) === String(eventId));
        if (!mounted) return;
        setRsvpStatus(mine ? mine.status : null);
      } catch (err) {
        if (!mounted) return;
        console.warn("Failed to load user RSVPs", err);
      }
    };
    loadMyRsvp();
    return () => {
      mounted = false;
    };
  }, [user, eventId, navigate]);

  /* Handler to create/update RSVP (status = 'Going'|'Interested'|'Not Going') */
  async function handleSetRsvp(status) {
    if (!user) {
      navigate("/login", { replace: true });
      return;
    }

    setRsvpError(null);
    const previous = rsvpStatus;
    setRsvpStatus(status);
    setRsvpLoading(true);

    try {
      const idToken = await user.getIdToken();
      const res = await createOrUpdateRsvp(idToken, Number(eventId), status);
      setRsvpStatus(res?.rsvp?.status ?? status);
    } catch (err) {
      setRsvpStatus(previous);
      setRsvpError(err.message || "Failed to update RSVP");
    } finally {
      setRsvpLoading(false);
    }
  }

  /* Handler to cancel RSVP */
  async function handleCancelRsvp() {
    if (!user) {
      navigate("/login", { replace: true });
      return;
    }

    setRsvpError(null);
    const previous = rsvpStatus;
    setRsvpStatus(null);
    setRsvpLoading(true);

    try {
      const idToken = await user.getIdToken();
      await deleteRsvp(idToken, Number(eventId));
      setRsvpStatus(null);
    } catch (err) {
      setRsvpStatus(previous);
      setRsvpError(err.message || "Failed to cancel RSVP");
    } finally {
      setRsvpLoading(false);
    }
  }

  if (loading) {
    return <div className="page-status">Loading Event...</div>;
  }

  if (error) {
    return <div className="page-status error">Error: {error}</div>;
  }

  if (!event) {
    return <div className="page-status">Event not found.</div>;
  }

  /* Once data is loaded, render the full page */
  const { name, color } =
    categoryDetails[event.category_id] || categoryDetails.default;
  const gmapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    event.location
  )}`;

  return (
    <main className="event-detail-page">
      <div className="event-detail-container">
        <Link to="/discover" className="back-link">
          ← Back to Discover
        </Link>

        <img
          src={
            event.image_url ||
            "https://placehold.co/1200x600/EEE/31343C?text=Townsquare+Event"
          }
          alt={event.title}
          className="event-hero-image"
        />

        <div className="event-header">
          <div className="event-title-section">
            <h1 className="event-title">{event.title}</h1>
            <div className="organizer-follow-section">
              <span className="organizer-label">
                Organized by: <strong>{organizer ? `@${organizer.username}` : 'Loading...'}</strong>
              </span>
              <FollowButton
                targetUid={event.organizer_uid}
                targetUsername={organizer?.username}
                className="event-follow-button"
              />
            </div>
          </div>
          <span
            className="event-category-tag"
            style={{ backgroundColor: color }}
          >
            {name}
          </span>
        </div>

        <div className="rsvp-container">
          {rsvpError && <div className="ts-error">{rsvpError}</div>}

          {rsvpStatus && rsvpStatus !== "Not Going" ? (
            <div style={{ marginBottom: 20, fontWeight: 600, fontSize: 20 }}>
              RSVP Status: {rsvpStatus}
            </div>
          ) : null}

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button
              className="rsvp-button"
              onClick={() => {
                if (!user) return navigate("/login", { replace: true });
                if (rsvpStatus === "Going") {
                  handleCancelRsvp();
                } else {
                  setIsRsvpOpen(true);
                }
              }}
              disabled={rsvpLoading}
            >
              {rsvpStatus === "Going"
                ? "Cancel RSVP"
                : rsvpStatus === "Interested"
                  ? "Update RSVP"
                  : "RSVP"}
            </button>
          </div>

          <RsvpModal
            isOpen={isRsvpOpen}
            onClose={() => setIsRsvpOpen(false)}
            initialStatus={rsvpStatus}
            onConfirm={(status) => handleSetRsvp(status)}
            loading={rsvpLoading}
            error={rsvpError}
          />
        </div>

        <div className="event-info-grid">
          <div className="info-item">
            <span className="info-icon">🗓️</span>
            <div>
              <strong>Date and Time</strong>
              <p>{formatEventTimeRange(event.start_time, event.end_time)}</p>
            </div>
          </div>
          <div className="info-item">
            <span className="info-icon">📍</span>
            <div>
              <strong>Location</strong>
              <p>
                {event.location}
                <a
                  href={gmapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="map-link"
                >
                  View on Map
                </a>
              </p>
            </div>
          </div>
          <div className="info-item">
            <span className="info-icon">👥</span>
            <div>
              <strong>Capacity</strong>
              <p>
                Up to{" "}
                {event.max_attendees > 0 ? event.max_attendees : "unlimited"}{" "}
                attendees
              </p>
            </div>
          </div>
        </div>

        <div className="event-description">
          <h2>About this Event</h2>
          <p>{event.description}</p>
        </div>
      </div>
    </main>
  );
}
