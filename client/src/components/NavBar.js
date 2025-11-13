import React, { useState } from "react";
import { NavLink, Link, useNavigate, useLocation } from "react-router-dom";
import CreateEventModal from "./CreateEvent";
import { useAuth } from "../auth/AuthContext";
import SearchBar from "./SearchBar";
import { useEvents } from "../contexts/EventContext";
import "./NavBar.css";

export default function NavBar() { 
  // create event modal is only visible to users
  const [openCreate, setOpenCreate] = useState (false);

  const { user, logout, initials } = useAuth();
  const { addEvent } = useEvents();
  const location = useLocation();

  // redirect after logout
  const nav = useNavigate();
  
  // redirect to /login if logging out
  const handleLogout = async () => {
    await logout();
    nav("/login", { replace: true })
  }

  // Handle event creation success
  const handleEventCreated = (newEvent) => {
    console.log("NEW EVENT CREATED:", newEvent);
    
    // Add the new event to the global state
    addEvent(newEvent);
    
    // Close the modal
    setOpenCreate(false);
    
    // If we're not on the discover page, navigate there to show the new event
    if (location.pathname !== "/discover" && location.pathname !== "/") {
      nav("/discover");
    }
  };

  return (
    <>
      <header className="ts-nav">
        <div className="ts-left">
          <Link to="/discover" className="ts-brand">Townsquare</Link>
        </div>

        <SearchBar />

        {/* <nav className="ts-center">
          <NavLink to="/discover" className="ts-tab">Discover</NavLink>
          <NavLink to="/following" className="ts-tab">Following</NavLink>
          <NavLink to="/saved" className="ts-tab">Saved Events</NavLink>
        </nav> */}

        <div className="ts-right">
          <button className="ts-btn" onClick={() => setOpenCreate(true)}>
            Create Event +
          </button>

          {/* avatar links to account profile */}
          <Link to="/profile" className="ts-avatar" aria-label="Open profile" title={user?.displayName || user?.email || "Account"}>
            {initials}
          </Link>

          <button className="ts-btn" onClick={handleLogout} aria-label="Log out">
            Log out
          </button>
        </div>
      </header>

      <CreateEventModal
        open={openCreate}
        onClose={() => setOpenCreate(false)}
        onCreate={handleEventCreated}
      />
    </>
  );
}
