import React, { useState, useEffect } from 'react';
import './Following.css';
import { getEvents } from '../api';
import SavedEvents from "../hooks/SavedEvents";
import EventCard from '../components/EventCard';
import { redirect } from 'react-router-dom';

export default function Following() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isSaved, toggleSaved } = SavedEvents();

  useEffect(() => {
    const fetchEvents = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getEvents();
            // We convert the object of events into an array
            const eventsArray = Object.values(response.events || {});
            setEvents(eventsArray);
        } catch (err) {
            setError(err.message || "An unexpected error occurred.");
        } finally {
            setLoading(false);
        }
      
    };
    fetchEvents();
  }, []);

  const renderContent = () => {
      if (loading) return <p className="ts-loading">Loading events...</p>;
      if (error) return <p className="ts-error">Error: {error}</p>;
      if (events.length === 0) return <p>No upcoming events found. Why not create one?</p>;

      return (
          <div className="event-grid">
                {events.map((event) => (
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
    <main className='main-container'>
      <div>
        <h1 className='page-header'>Following</h1>
        <p className='page-subheading'>Events from people and organizations you follow</p>
      </div>
      
      {/* Friends Section */}
      <div>
        <h2 className='friends-header'>Events with People You Follow</h2>
        <div>
          {renderContent()}
        </div>
      </div>

      {/* Organizations Section */}
      <div>
        <h2 className='orgs-header'>Events from Organizations You Follow</h2>
        <div>
          {renderContent()}
        </div>
      </div>
    </main>
  )
}
