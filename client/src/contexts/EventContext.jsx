import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { useSearchParams } from "react-router-dom";
import { getEvents } from "../api";

const EventContext = createContext(null);

export function EventProvider({ children }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const successTimeoutRef = useRef(null);
  const [searchParams] = useSearchParams();
  const searchParamsString = searchParams.toString();
  const lastFiltersRef = useRef(null);
  const currentControllerRef = useRef(null);

  // Clear success message after a delay
  const showSuccessMessage = (message) => {
    // Clear any existing timeout to prevent stale state updates
    if (successTimeoutRef.current) {
      clearTimeout(successTimeoutRef.current);
    }

    setSuccessMessage(message);
    successTimeoutRef.current = setTimeout(() => {
      setSuccessMessage(null);
      successTimeoutRef.current = null;
    }, 3000);
  };

  // Fetch events; accepts optional filters override and options ({ signal })
  const fetchEvents = useCallback(
    async (filtersOverride = null, { signal } = {}) => {
      try {
        setLoading(true);
        setError(null);

        // Build filters from override or from current search params string
        const filters =
          filtersOverride ??
          (() => {
            const f = {};
            const params = new URLSearchParams(searchParamsString);
            const q = params.get("q");
            if (q) f.q = q;
            const page = params.get("page");
            if (page) f.page = Number(page);
            const per_page =
              params.get("per_page") ||
              params.get("pageSize") ||
              params.get("page_size");
            if (per_page) f.pageSize = Number(per_page);
            const category_id = params.get("category_id");
            if (category_id) f.category_id = category_id;
            const start_date = params.get("start_date");
            if (start_date) f.start_date = start_date;
            const end_date = params.get("end_date");
            if (end_date) f.end_date = end_date;
            const tags = params.getAll("tags");
            if (tags.length) f.tags = tags;
            return f;
          })();

        // remember last used filters for refreshEvents
        lastFiltersRef.current = filters;

        const response = await getEvents(filters, { signal });
        const eventsArray = Array.isArray(response.events)
          ? response.events
          : Object.values(response.events || {});
        setEvents(eventsArray);
      } catch (err) {
        if (err?.name === "AbortError") return; // cancelled
        setError(err?.message || "Failed to fetch events");
        setEvents([]);
      } finally {
        setLoading(false);
      }
    },
    [searchParamsString]
  );

  // Add a new event to the list (add it at the beginning for visibility)
  const addEvent = (newEvent) => {
    setEvents((prevEvents) => [newEvent, ...prevEvents]);
    showSuccessMessage(`"${newEvent.title}" has been created successfully!`);
  };

  // Update an existing event
  const updateEvent = (updatedEvent) => {
    setEvents((prevEvents) =>
      prevEvents.map((event) =>
        event.event_id === updatedEvent.event_id ? updatedEvent : event
      )
    );
  };

  // Remove an event from the list
  const removeEvent = (eventId) => {
    setEvents((prevEvents) =>
      prevEvents.filter((event) => event.event_id !== eventId)
    );
  };

  // Refresh events (useful for manual refresh)
  const refreshEvents = (filtersOverride = null) => {
    // cancel any current request
    if (currentControllerRef.current) {
      try {
        currentControllerRef.current.abort();
      } catch (e) {}
      currentControllerRef.current = null;
    }
    const controller = new AbortController();
    currentControllerRef.current = controller;

    // Use provided override or last used filters
    const useFilters = filtersOverride ?? lastFiltersRef.current;
    fetchEvents(useFilters, { signal: controller.signal });
  };

  // Fetch whenever the URL search params change (or on mount)
  useEffect(() => {
    // cancel previous
    if (currentControllerRef.current) {
      try {
        currentControllerRef.current.abort();
      } catch (e) {}
      currentControllerRef.current = null;
    }

    const controller = new AbortController();
    currentControllerRef.current = controller;

    fetchEvents(null, { signal: controller.signal });

    return () => {
      try {
        controller.abort();
      } catch (e) {}
      currentControllerRef.current = null;
    };
  }, [fetchEvents]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (successTimeoutRef.current) {
        clearTimeout(successTimeoutRef.current);
      }
    };
  }, []);

  const value = {
    events,
    loading,
    error,
    successMessage,
    addEvent,
    updateEvent,
    removeEvent,
    refreshEvents,
    fetchEvents,
  };

  return (
    <EventContext.Provider value={value}>{children}</EventContext.Provider>
  );
}

export function useEvents() {
  const context = useContext(EventContext);
  if (!context) {
    throw new Error("useEvents must be used within an EventProvider");
  }
  return context;
}
