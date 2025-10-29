import React, { createContext, useContext, useState, useEffect, useRef } from "react";
import { getAllEvents } from "../api";

const EventContext = createContext(null);

export function EventProvider({ children }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const successTimeoutRef = useRef(null);

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

  // Fetch all events
  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getAllEvents();
      const eventsArray = Object.values(response.events || {});
      setEvents(eventsArray);
    } catch (err) {
      setError(err.message || "Failed to fetch events");
    } finally {
      setLoading(false);
    }
  };

  // Add a new event to the list (add it at the beginning for visibility)
  const addEvent = (newEvent) => {
    setEvents(prevEvents => [newEvent, ...prevEvents]);
    showSuccessMessage(`"${newEvent.title}" has been created successfully!`);
  };

  // Update an existing event
  const updateEvent = (updatedEvent) => {
    setEvents(prevEvents => 
      prevEvents.map(event => 
        event.event_id === updatedEvent.event_id ? updatedEvent : event
      )
    );
  };

  // Remove an event from the list
  const removeEvent = (eventId) => {
    setEvents(prevEvents => 
      prevEvents.filter(event => event.event_id !== eventId)
    );
  };

  // Refresh events (useful for manual refresh)
  const refreshEvents = () => {
    fetchEvents();
  };

  // Initial load
  useEffect(() => {
    fetchEvents();
  }, []);

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
    fetchEvents
  };

  return (
    <EventContext.Provider value={value}>
      {children}
    </EventContext.Provider>
  );
}

export function useEvents() {
  const context = useContext(EventContext);
  if (!context) {
    throw new Error("useEvents must be used within an EventProvider");
  }
  return context;
}