import React from "react";
import { Link } from "react-router-dom";
import SavedEvents from "../hooks/SavedEvents";
import "./SavedEventsPage.css"; // optional, see styles below
import EventCard from "../components/EventCard";

// Helpers for date filtering
const toDate = (iso) => (iso ? new Date(iso) : null);
const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const inRange = (d, from, to) => {
  if (!d) return false;
  const day = startOfDay(d);
  if (from && day < startOfDay(from)) return false;
  if (to && day > startOfDay(to)) return false;
  return true;
};

// Same layout grid of discover,  local time range formatter
// eslint-disable-next-line no-unused-vars
const formatRange = (startStr, endStr) => {
  const s = new Date(startStr);
  const e = endStr ? new Date(endStr) : s;
  const o = {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  };
  const a = s.toLocaleDateString("en-US", o);
  if (s.toDateString() === e.toDateString()) {
    const b = e.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
    return `${a} - ${b}`;
  }
  const b = e.toLocaleDateString("en-US", o);
  return `${a} to ${b}`;
};

export default function SavedEventsPage() {
  // From the localStorage-backed hook: savedList, isSaved, toggleSaved
  const { savedList, toggleSaved, isSaved } = SavedEvents();

  const [status, setStatus] = React.useState("all"); // all | upcoming | ongoing | past
  const [from, setFrom] = React.useState(null); // Date | null
  const [to, setTo] = React.useState(null); // Date | null
  const [sort, setSort] = React.useState("soonest"); // soonest | latest | title

  // Derive a filtered/sorted copy for rendering
  const filtered = React.useMemo(() => {
    const now = new Date();
    const items = [...savedList];

    // status filter
    const keepByStatus = (ev) => {
      const s = toDate(ev.start_time);
      const e = toDate(ev.end_time) || s;
      if (!s) return false;
      if (status === "upcoming") return s > now;
      if (status === "past") return e < now;
      if (status === "ongoing") return s <= now && e >= now;
      return true; // "all"
    };

    // date range filter (inclusive by day, based on start_time)
    const keepByRange = (ev) => {
      const s = toDate(ev.start_time);
      return inRange(s, from, to);
    };

    const afterStatus = items.filter(keepByStatus);
    const afterRange =
      from || to ? afterStatus.filter(keepByRange) : afterStatus;

    // sorting
    afterRange.sort((a, b) => {
      if (sort === "title") {
        return (a.title || "").localeCompare(b.title || "");
      }
      const ad = toDate(a.start_time)?.getTime() ?? 0;
      const bd = toDate(b.start_time)?.getTime() ?? 0;
      return sort === "latest" ? bd - ad : ad - bd; // default = "soonest"
    });

    return afterRange;
  }, [savedList, status, from, to, sort]);

  return (
    <main className="ts-page">
      <h1 className="ts-title">Saved Events</h1>
      <p className="ts-subtitle">Your favorites, all in one place</p>

      <section
        className="sv-controls compact"
        aria-label="Saved events filters"
      >
        <div className="sv-row sv-row-right">
          <label className="sv-label">
            <span>Status</span>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="sv-input"
            >
              <option value="all">All</option>
              <option value="upcoming">Upcoming</option>
              <option value="ongoing">Ongoing</option>
              <option value="past">Past</option>
            </select>
          </label>

          <label className="sv-label">
            <span>From</span>
            <input
              type="date"
              value={from ? startOfDay(from).toISOString().slice(0, 10) : ""}
              onChange={(e) =>
                setFrom(e.target.value ? new Date(e.target.value) : null)
              }
              className="sv-input"
              placeholder="mm/dd/yyyy"
            />
          </label>

          <label className="sv-label">
            <span>To</span>
            <input
              type="date"
              value={to ? startOfDay(to).toISOString().slice(0, 10) : ""}
              onChange={(e) =>
                setTo(e.target.value ? new Date(e.target.value) : null)
              }
              className="sv-input"
              placeholder="mm/dd/yyyy"
            />
          </label>

          <label className="sv-label sv-grow">
            <span>Sort</span>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="sv-input"
            >
              <option value="soonest">Date (soonest)</option>
              <option value="latest">Date (latest)</option>
              <option value="title">Title (A–Z)</option>
            </select>
          </label>
        </div>
      </section>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="sv-empty">
          No saved events matching your filters.{" "}
          <Link className="pf-linkbtn" to="/discover">
            Discover events
          </Link>
        </div>
      ) : (
        <div className="event-grid">
          {filtered.map((ev) => (
            <EventCard
              key={ev.event_id}
              event={ev}
              isSaved={isSaved}
              onToggleSaved={toggleSaved}
            />
          ))}
        </div>
      )}
    </main>
  );
}
