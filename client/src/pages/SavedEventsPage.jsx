import React from "react";
import { Link } from "react-router-dom";
import SavedEvents from "../hooks/SavedEvents";
import "./SavedEventsPage.css"; // optional, see styles below

// Same layout grid of discover
const fmt = (s, e) => {
  const sd = new Date(s), ed = new Date(e);
  const o = { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };
  const a = sd.toLocaleDateString('en-US', o);
  if (sd.toDateString() === ed.toDateString()) {
    const b = ed.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    return `${a} - ${b}`;
  }
  const b = ed.toLocaleDateString('en-US', o);
  return `${a} to ${b}`;
};

export default function SavedEventsPage() {
  const { savedList, toggleSaved, isSaved } = SavedEvents();

  return (
    <main className="ts-page">
      <h1 className="ts-title">Saved Events</h1>
      <p className="ts-subtitle">Your favorites, all in one place</p>

      {savedList.length === 0 ? (
        <div className="sv-empty">
          Nothing saved yet. <Link className="pf-linkbtn" to="/discover">Discover events</Link>
        </div>
      ) : (
        <div className="event-grid">
          {savedList.map(ev => (
            <Link to={`/events/${ev.event_id}`} key={ev.event_id} className="event-card">
              <div className="event-card-image-wrapper">
                <img
                  src={ev.image_url || 'https://placehold.co/600x400/EEE/31343C?text=Townsquare'}
                  alt={ev.title}
                  className="event-card-image"
                />
                <button
                  className={`event-save ${isSaved(ev.event_id) ? "saved" : ""}`}
                  aria-pressed={isSaved(ev.event_id)}
                  aria-label="Unsave event"
                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); toggleSaved(ev); }}
                  title="Remove from Saved"
                >
                  <span className="material-symbols-outlined event-heart">favorite</span>
                </button>
              </div>

              <div className="event-card-body">
                <h3 className="event-card-title">{ev.title}</h3>
                <p className="event-card-time">{fmt(ev.start_time, ev.end_time)}</p>
                <p className="event-card-location">{ev.location}</p>
                <p className="event-card-description">
                  {ev.description?.length > 100 ? ev.description.slice(0,100) + "…" : ev.description}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
