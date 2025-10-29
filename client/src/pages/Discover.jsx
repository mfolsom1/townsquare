// Discover.js: Page for discovering events
import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getEvents } from "../api"; // Make sure the path to your api.js is correct
import "./Discover.css";
import SavedEvents from "../hooks/SavedEvents";
import EventCard from "../components/EventCard";

// --- Main Discover Page Component ---

export default function Discover() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { isSaved, toggleSaved } = SavedEvents();
    const [searchParams] = useSearchParams();

    useEffect(() => {
        const fetchEvents = async () => {
            setLoading(true);
            setError(null);
            try {
                const filters = {};
                const q = searchParams.get('q'); if (q) filters.q = q;
                const page = searchParams.get('page'); if (page) filters.page = page;
                const per_page = searchParams.get('per_page'); if (per_page) filters.per_page = per_page;
                const category_id = searchParams.get('category_id'); if (category_id) filters.category_id = category_id;
                const start_date = searchParams.get('start_date'); if (start_date) filters.start_date = start_date;
                const end_date = searchParams.get('end_date'); if (end_date) filters.end_date = end_date;
                const tags = searchParams.getAll('tags'); if (tags.length) filters.tags = tags;
                // The API now returns an object where keys are event IDs
                // const response = await getAllEvents();
                const response = await getEvents(filters);
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
    }, [searchParams]);

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
        <main className="ts-page">
            <h1 className="ts-title">Discover Events</h1>
            <p className="ts-subtitle">Find out what's happening in your community</p>
            {renderContent()}
        </main>
    );
}