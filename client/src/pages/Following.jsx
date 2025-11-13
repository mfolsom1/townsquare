import React, { useState, useEffect } from "react";
import "./Following.css";
import { getFriendEvents, getFriendCreatedEvents, getFollowedOrganizations, getOrganizationEvents } from "../api";
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

        // Fetch events from friends (both attending/interested and created)
        const [friendAttendingResponse, friendCreatedResponse] = await Promise.all([
          getFriendEvents(idToken),
          getFriendCreatedEvents(idToken)
        ]);
        
        const friendAttendingEvents = Array.isArray(friendAttendingResponse.events)
          ? friendAttendingResponse.events
          : [];
        const friendCreatedEvents = Array.isArray(friendCreatedResponse.events)
          ? friendCreatedResponse.events
          : [];
        
        // Combine and deduplicate events using event_id
        const allFriendEvents = [...friendAttendingEvents, ...friendCreatedEvents];
        const uniqueFriendEvents = allFriendEvents.filter((event, index, self) =>
          index === self.findIndex(e => e.event_id === event.event_id)
        );
        
        if (mounted) setFriendEvents(uniqueFriendEvents);

        // Fetch events from followed organizations
        const followedOrgsResponse = await getFollowedOrganizations(idToken);
        const followedOrgs = followedOrgsResponse.organizations || [];
        
        // Fetch events from all followed organizations
        const orgEventPromises = followedOrgs.map(org => 
          getOrganizationEvents(org.org_id)
        );
        const orgEventResponses = await Promise.all(orgEventPromises);
        const allOrgEvents = orgEventResponses.flatMap(response => 
          Array.isArray(response.events) ? response.events : []
        );
        
        if (mounted) setOrgEvents(allOrgEvents);
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
    <main className="main-container">
      <div>
        <h1 className="page-header">Following</h1>
        <p className="page-subheading">
          Events from people and organizations you follow
        </p>
      </div>

      {/* Show loading/error states */}
      {loading && <p className="ts-loading">Loading events...</p>}
      {error && <p className="ts-error">Error: {error}</p>}

      {/* Only show content when not loading and no error */}
      {!loading && !error && (
        <>
          {/* Friends Section */}
          <div>
            <h2 className="friends-header">Events from People You Follow</h2>
            <div>
              {friendEvents.length > 0 ? (
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
              ) : (
                <p className="no-events-message">
                  No events from people you follow. Try following some users to see their events here!
                </p>
              )}
            </div>
          </div>

          {/* Organizations Section */}
          <div>
            <h2 className="orgs-header">Events from Organizations You Follow</h2>
            <div>
              {orgEvents.length > 0 ? (
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
              ) : (
                <p className="no-events-message">
                  No events from organizations you follow. Try following some organizations to see their events here!
                </p>
              )}
            </div>
          </div>
        </>
      )}
    </main>
  );
}
