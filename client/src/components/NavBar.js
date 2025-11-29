import React, { useState } from "react";
import { Link, NavLink, useNavigate, useLocation } from "react-router-dom";
import CreateEventModal from "./CreateEvent";
import { useAuth } from "../auth/AuthContext";
import SearchBar from "./SearchBar";
import { useEvents } from "../contexts/EventContext";
import { getUserProfile } from "../api";
import "./NavBar.css";
import logo from "../assets/townsquare-logo.png";


export default function NavBar() {
  // create event modal is only visible to users
  const [openCreate, setOpenCreate] = useState(false);

  const { user, logout, initials } = useAuth();
  const [error, setError] = useState("");
  const [userProfile, setUserProfile] = useState(null);
  const { addEvent } = useEvents();
  const location = useLocation();

  // Check if user is organization
  const isOrganization = userProfile?.user_type === 'organization' || userProfile?.userType === 'organization';
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
        {/* Left: Logo */}
        <div className="ts-left">
          <Link to="/discover" className="ts-brand-wrap">
            <img src={logo} alt="Townsquare Logo" className="ts-logo" />
            <span className="ts-brand">Townsquare</span>
          </Link>
        </div>



        {/* Center: tabs */}
        <nav className="ts-center">
          <NavLink to="/discover" className="ts-tab">
            Discover
          </NavLink>
          <NavLink to="/following" className="ts-tab">
            Following
          </NavLink>
          <NavLink to="/saved" className="ts-tab">
            Saved Events
          </NavLink>
        </nav>

        {/* Right: search + create + avatar + logout */}
        <div className="ts-right">
          <div className="ts-search">
            <SearchBar />
          </div>

          <button
            className="ts-btn ts-btn-primary"
            onClick={() => setOpenCreate(true)}
          >
            Create Event
          </button>


          {/* avatar links to account profile */}
          <Link to={isOrganization ? "/dashboard" : "/profile"} className="ts-avatar" aria-label="Open profile" title={user?.displayName || user?.email || "Account"}>
            {initials}
          </Link>

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