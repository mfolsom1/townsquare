import React, { useState, useEffect } from "react";
import "./Following.css";
import { getFriendEvents, getFriendCreatedEvents } from "../api";
import { useAuth } from "../auth/AuthContext";
import { useNavigate } from "react-router-dom";
import SavedEvents from "../hooks/SavedEvents";
import EventCard from "../components/EventCard";

export default function Following() {
  const [friendRsvpEvents, setFriendRsvpEvents] = useState([]);
  const [friendCreatedEvents, setFriendCreatedEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isSaved, toggleSaved } = SavedEvents();
  const { user } = useAuth();

  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;

    const fetchEvents = async () => {
      setLoading(true);
      setError(null);
      try {
        if (!user) {
          navigate("/login", { replace: true });
          return;
        }

        const idToken = await user.getIdToken();

        /* Fetch events from friends: RSVPs and created events */
        const [rsvpResponse, createdResponse] = await Promise.all([
          getFriendEvents(idToken),
          getFriendCreatedEvents(idToken)
        ]);

        const friendRsvpData = Array.isArray(rsvpResponse.events)
          ? rsvpResponse.events
          : [];

        const friendCreatedData = Array.isArray(createdResponse.events)
          ? createdResponse.events
          : [];

        if (mounted) {
          setFriendRsvpEvents(friendRsvpData);
          setFriendCreatedEvents(friendCreatedData);
        }
      } catch (err) {
        if (mounted) setError(err.message || "An unexpected error occurred.");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchEvents();
    return () => {
      mounted = false;
    };
  }, [user, navigate]);

  return (
    <main className="ts-page">
      <div>
        <h1 className="ts-title">Following</h1>
        <p className="ts-subtitle">
          Events from people you follow
        </p>
      </div>

      {loading && <p className="ts-loading">Loading events...</p>}
      {error && <p className="ts-error">Error: {error}</p>}

      {!loading && !error && (
        <>
          {/* Friends RSVP Section */}
          <div>
            <h2 className="friends-header">Friends' RSVPs</h2>
            <div>
              {friendRsvpEvents.length > 0 ? (
                <div className="event-grid">
                  {friendRsvpEvents.map((event) => (
                    <EventCard
                      key={event.event_id}
                      event={event}
                      isSaved={isSaved}
                      onToggleSaved={toggleSaved}
                    />
                  ))}
                </div>
              ) : (
                <p className="no-events-message">
                  No events from people you follow at the moment. Start following more friends!
                </p>
              )}
            </div>
          </div>

          {/* Friends Created Events Section */}
          <div>
            <h2 className="friends-header">Events Created by Friends</h2>
            <div>
              {friendCreatedEvents.length > 0 ? (
                <div className="event-grid">
                  {friendCreatedEvents.map((event) => (
                    <EventCard
                      key={event.event_id}
                      event={event}
                      isSaved={isSaved}
                      onToggleSaved={toggleSaved}
                    />
                  ))}
                </div>
              ) : (
                <p className="no-events-message">
                  No events created by people you follow. Encourage them to organize something!
                </p>
              )}
            </div>
          </div>
        </>
      )}
    </main>
  );
}

