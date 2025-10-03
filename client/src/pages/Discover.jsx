// Discover.js: Page for discovering events
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAllEvents } from "../api"; // Make sure the path to your api.js is correct
import "./Discover.css";

// --- Helper Data & Functions ---

// Maps category IDs to human-readable names and colors for styling the badge
const categoryDetails = {
    1: { name: "Tech", color: "#007BFF" },
    2: { name: "Music", color: "#E83E8C" },
    3: { name: "Art & Culture", color: "#FD7E14" },
    4: { name: "Food & Drink", color: "#28A745" },
    5: { name: "Community", color: "#17A2B8" },
    default: { name: "General", color: "#6C757D" }
};

/**
 * Formats a start and end time into a clear, readable range.
 * Handles events that span across different days.
 * @param {string} startStr - The ISO start time.
 * @param {string} endStr - The ISO end time.
 * @returns {string} A formatted time range string.
 */
const formatEventTimeRange = (startStr, endStr) => {
    const startDate = new Date(startStr);
    const endDate = new Date(endStr);
    const options = { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };

    const startFormatted = startDate.toLocaleDateString('en-US', options);

    // If the event ends on the same day, only show the end time
    if (startDate.toDateString() === endDate.toDateString()) {
        const endFormatted = endDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
        return `${startFormatted} - ${endFormatted}`;
    }
    
    // If it ends on a different day, show the full end date and time
    const endFormatted = endDate.toLocaleDateString('en-US', options);
    return `${startFormatted} to ${endFormatted}`;
};


// --- Sub-components ---

/**
 * EventCard Component: Displays a single event with all its details.
 * This component is designed to be clickable, leading to the event's detail page.
 */
const EventCard = ({ event }) => {
    const { name, color } = categoryDetails[event.category_id] || categoryDetails.default;

    // Truncate long descriptions to keep the card clean
    const shortDescription = event.description.length > 100
        ? event.description.substring(0, 100) + "..."
        : event.description;

    return (
        <Link to={`/events/${event.event_id}`} className="event-card">
            {/* Image container with a category badge */}
            <div className="event-card-image-wrapper">
                <img
                    src={event.image_url || 'https://placehold.co/600x400/EEE/31343C?text=Townsquare'}
                    alt={event.title}
                    className="event-card-image"
                />
                <span className="event-card-category-badge" style={{ backgroundColor: color }}>
                    {name}
                </span>
            </div>
            
            {/* Main content of the card */}
            <div className="event-card-body">
                <h3 className="event-card-title">{event.title}</h3>
                <p className="event-card-time">{formatEventTimeRange(event.start_time, event.end_time)}</p>
                <p className="event-card-location">{event.location}</p>
                <p className="event-card-description">{shortDescription}</p>
                
                {/* Attendee info, only shown if max_attendees is set */}
                {event.max_attendees > 0 && (
                    <div className="event-card-attendees">
                        {/* A simple user icon SVG */}
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                        </svg>
                        <span>Up to {event.max_attendees} people</span>
                    </div>
                )}
            </div>
        </Link>
    );
};


// --- Main Discover Page Component ---

export default function Discover() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchEvents = async () => {
            try {
                // The API now returns an object where keys are event IDs
                const response = await getAllEvents();
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
                {events.map(event => (
                    <EventCard key={event.event_id} event={event} />
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