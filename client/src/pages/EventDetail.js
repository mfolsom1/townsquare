import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getEventById } from '../api'; // Make sure the path to your api.js is correct
import './EventDetail.css';

// Re-using the same helpers from the Discover page for consistency
const categoryDetails = {
    1: { name: "Tech", color: "#007BFF" },
    2: { name: "Music", color: "#E83E8C" },
    // ... add all other categories
    default: { name: "General", color: "#6C757D" }
};

const formatEventTimeRange = (startStr, endStr) => {
    const startDate = new Date(startStr);
    const endDate = new Date(endStr);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    const startFormatted = startDate.toLocaleDateString('en-US', options);
    const endFormatted = endDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    return `${startFormatted} to ${endFormatted}`;
};


export default function EventDetail() {
    const { eventId } = useParams(); // Gets the event's ID from the URL
    const [event, setEvent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchEvent = async () => {
            try {
                const response = await getEventById(eventId);
                setEvent(response.event);
            } catch (err) {
                setError(err.message || "Failed to load event details.");
            } finally {
                setLoading(false);
            }
        };

        fetchEvent();
    }, [eventId]); // Re-run the effect if the eventId changes

    if (loading) {
        return <div className="page-status">Loading Event...</div>;
    }

    if (error) {
        return <div className="page-status error">Error: {error}</div>;
    }
    
    if (!event) {
        return <div className="page-status">Event not found.</div>;
    }
    
    // Once data is loaded, render the full page
    const { name, color } = categoryDetails[event.category_id] || categoryDetails.default;
    const gmapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(event.location)}`;

    return (
        <main className="event-detail-page">
            <div className="event-detail-container">
                <Link to="/discover" className="back-link">← Back to Discover</Link>
                
                <img 
                    src={event.image_url || 'https://placehold.co/1200x600/EEE/31343C?text=Townsquare+Event'} 
                    alt={event.title} 
                    className="event-hero-image" 
                />

                <div className="event-header">
                    <h1 className="event-title">{event.title}</h1>
                    <span className="event-category-tag" style={{ backgroundColor: color }}>{name}</span>
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
                                <a href={gmapsUrl} target="_blank" rel="noopener noreferrer" className="map-link">View on Map</a>
                            </p>
                        </div>
                    </div>
                     <div className="info-item">
                        <span className="info-icon">👥</span>
                        <div>
                            <strong>Capacity</strong>
                            <p>Up to {event.max_attendees > 0 ? event.max_attendees : 'unlimited'} attendees</p>
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