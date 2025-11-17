import React from "react";
import { Link } from "react-router-dom";

const categoryDetails = {
  1: { name: "Gator Sports", color: "#FA4616" },
  2: { name: "UF Campus Life", color: "#0021A5" },
  3: { name: "Local Music & Arts", color: "#FFC300" },
  4: { name: "Outdoor & Nature", color: "#1A9956" },
  5: { name: "Food & Breweries", color: "#900C3F" },
  6: { name: "Community & Markets", color: "#581845" },
  7: { name: "Tech & Innovation", color: "#2A6E99" },
  default: { name: "General", color: "#6C757D" }
};

const formatEventTimeRange = (startStr, endStr) => {
  const startDate = new Date(startStr);
  const endDate = new Date(endStr);
  const options = { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" };
  const startFormatted = startDate.toLocaleDateString("en-US", options);

  if (startDate.toDateString() === endDate.toDateString()) {
    const endFormatted = endDate.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    return `${startFormatted} - ${endFormatted}`;
  }

  const endFormatted = endDate.toLocaleDateString("en-US", options);
  return `${startFormatted} to ${endFormatted}`;
};

export default function EventCard({ event, isSaved, onToggleSaved }) {
  const { name, color } = categoryDetails[event.category_id] || categoryDetails.default;

  const description = event.description || "";
  const shortDescription = description.length > 100 ? description.substring(0, 100) + "..." : description;

  const saved = isSaved(event.event_id);
  const onHeartClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onToggleSaved(event);
  };

  console.log("EventCard received:", event);

  return (
    <Link to={`/events/${event.event_id}`} className="event-card">
      <div className="event-card-image-wrapper">
        <img
          src={event.image_url || "https://placehold.co/600x400/EEE/31343C?text=Townsquare"}
          alt={event.title}
          className="event-card-image"
        />

        <button
          className={`event-save ${saved ? "saved" : ""}`}
          aria-pressed={saved}
          aria-label={saved ? "Unsave event" : "Save event"}
          onClick={onHeartClick}
          title={saved ? "Remove from Saved" : "Save to Saved"}
        >
          <span className="material-symbols-outlined event-heart">favorite</span>
        </button>

        <span className="event-card-category-badge" style={{ backgroundColor: color }}>
          {name}
        </span>
      </div>

      <div className="event-card-body">
        <h3 className="event-card-title">{event.title}</h3>
        <p className="event-card-time">{formatEventTimeRange(event.start_time, event.end_time)}</p>
        <p className="event-card-location">{event.location}</p>
        <p className="event-card-description">{shortDescription}</p>

        {event.max_attendees > 0 && (
          <div className="event-card-attendees">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
            </svg>
            <span>Up to {event.max_attendees} people</span>
          </div>
        )}
      </div>
    </Link>
  );
}