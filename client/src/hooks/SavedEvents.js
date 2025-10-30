import { useCallback, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "ts_saved_events_v1";

/** Stores a lightweight copy of the event so Saved page can render without refetching. */
export default function SavedEvents() {
  const [saved, setSaved] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  });

  // persist to localStorage
  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(saved)); } catch {}
  }, [saved]);

  const isSaved = useCallback(
    (eventId) => Boolean(saved[eventId]),
    [saved]
  );

  const toggleSaved = useCallback((eventObj) => {
    setSaved((prev) => {
      const next = { ...prev };
      const id = eventObj.event_id;
      if (next[id]) {
        delete next[id];
      } else {
        // store minimal fields we need on Saved page
        next[id] = {
          event_id: eventObj.event_id,
          title: eventObj.title,
          description: eventObj.description || "",
          image_url: eventObj.image_url || "",
          location: eventObj.location || "",
          start_time: eventObj.start_time,
          end_time: eventObj.end_time,
          category_id: eventObj.category_id,
          max_attendees: eventObj.max_attendees ?? 0,
        };
      }
      return next;
    });
  }, []);

  const savedList = useMemo(
    () => Object.values(saved), [saved]
  );

  return { isSaved, toggleSaved, savedList };
}
