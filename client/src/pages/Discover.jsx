// src/pages/Discover.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./Discover.css";
import { subscribeToEvents } from "../services/eventsApi";

/* Robust formatter */
const DATE_FMT = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
const TIME_FMT = new Intl.DateTimeFormat([], { hour: "numeric", minute: "2-digit" });

function fmtDateTime(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) {
    return { date: String(iso), time: "" };
  }
  const year = d.getFullYear(); // always 4 digits
  return { date: `${DATE_FMT.format(d)}, ${year}`, time: TIME_FMT.format(d) };
}

export default function Discover() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsub = subscribeToEvents(rows => {
      setItems(rows);
      setLoading(false);
    });
    return unsub;
  }, []);

  function toggleSave(id) {
    setItems(prev =>
      prev.map(ev => (ev.id === id ? { ...ev, saved: !ev.saved } : ev))
    );
  }

  return (
    <div className="ts-discover">
      <header className="ts-discover__header">
        <h1>Recommended For You</h1>
        <p>Based on your interests and activity</p>
      </header>

      <section className="ts-grid">
        {loading &&
          Array.from({ length: 8 }).map((_, i) => (
            <div key={`sk-${i}`} className="ts-card ts-card--skeleton" />
          ))}

        {!loading &&
          items.map(ev => (
            <article key={ev.id} className="ts-card" aria-label={ev.title}>
              <div className={`ts-card__media ${ev.coverUrl ? "" : "is-placeholder"}`}>
                {ev.coverUrl ? (
                  <img src={ev.coverUrl} alt={ev.title} loading="lazy" />
                ) : (
                  <div className="ts-ph">Event</div>
                )}

                {ev.category && <span className="ts-badge">{ev.category}</span>}

                <button
                  className={`ts-heart ${ev.saved ? "is-saved" : ""}`}
                  onClick={() => toggleSave(ev.id)}
                  aria-pressed={ev.saved}
                  aria-label={ev.saved ? "Unsave" : "Save"}
                >
                  <span className="material-symbols-outlined ts-icon" aria-hidden="true">
                    favorite
                  </span>
                </button>
              </div>

              <div className="ts-card__body">
                <h3 className="ts-card__title">{ev.title}</h3>
                {ev.desc && <p className="ts-card__desc">{ev.desc}</p>}

                {ev.startAt && (
                  <div className="ts-card__meta">
                    <span className="material-symbols-outlined ts-icon" aria-hidden="true">
                      calendar_today
                    </span>
                    {(() => {
                      const { date, time } = fmtDateTime(ev.startAt);
                      return <span>{date} {" · "} {time}</span>;
                    })()}
                  </div>
                )}

                {ev.location && (
                  <div className="ts-card__meta">
                    <span className="material-symbols-outlined ts-icon" aria-hidden="true">
                      location_on
                    </span>
                    <span className="ts-ellipsis">{ev.location}</span>
                  </div>
                )}

                <Link to={`/events/${ev.id}`} className="ts-btn">
                  View Details
                </Link>
              </div>
            </article>
          ))}
      </section>

      {!loading && items.length === 0 && (
        <div className="ts-empty">No events yet — create the first one!</div>
      )}
    </div>
  );
}