import React, { useState, useEffect } from "react";
import "./Following.css";
import { getFriendEvents, getFriendCreatedEvents } from "../api";
import { useAuth } from "../auth/AuthContext";
import { useNavigate } from "react-router-dom";
import SavedEvents from "../hooks/SavedEvents";
import EventCard from "../components/EventCard";

export default function Following() {
  const [friendEvents, setFriendEvents] = useState([]);
  const [orgEvents, setOrgEvents] = useState([]);
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
        // If the user is not logged in, mirror ProfileContainer and redirect to login
        if (!user) {
          navigate("/login", { replace: true });
          return;
        }

        const idToken = await user.getIdToken();

        const response1 = await getFriendEvents(idToken);
        const friendEventsArray = Array.isArray(response1.events)
          ? response1.events
          : [];
        if (mounted) setFriendEvents(friendEventsArray);

        const response2 = await getFriendCreatedEvents(idToken);
        const createdEventsArray = Array.isArray(response2.events)
          ? response2.events
          : [];
        if (mounted) setOrgEvents(createdEventsArray);
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

  const renderContent = () => {
    if (loading) return <p className="ts-loading">Loading events...</p>;
    if (error) return <p className="ts-error">Error: {error}</p>;

    return (
      <div className="event-grid">
        {friendEvents.map((event) => (
          <EventCard
            key={event.event_id}
            event={event}
            isSaved={isSaved}
            onToggleSaved={toggleSaved}
          />
        ))}
      </div>
    );
  };

  return (
    <main className="main-container">
      <div>
        <h1 className="page-header">Following</h1>
        <p className="page-subheading">
          Events from people and organizations you follow
        </p>
      </div>

      {/* Friends Section */}
      <div>
        <h2 className="friends-header">Events with People You Follow</h2>
        <div>
          {loading && <p className="ts-loading">Loading events...</p>}
          {error && <p className="ts-error">Error: {error}</p>}
          {!loading && !error && (
            <div className="event-grid">
              {friendEvents.map((event) => (
                <EventCard
                  key={event.event_id}
                  event={event}
                  isSaved={isSaved}
                  onToggleSaved={toggleSaved}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Organizations Section */}
      <div>
        <h2 className="orgs-header">Events from Organizations You Follow</h2>
        <div>
          {loading && <p className="ts-loading">Loading events...</p>}
          {error && <p className="ts-error">Error: {error}</p>}
          {!loading && !error && (
            <div className="event-grid">
              {orgEvents.map((event) => (
                <EventCard
                  key={event.event_id}
                  event={event}
                  isSaved={isSaved}
                  onToggleSaved={toggleSaved}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
