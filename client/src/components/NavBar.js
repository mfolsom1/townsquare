// src/components/NavBar.jsx
import React, { useState } from "react";
import { NavLink, Link, useNavigate, useLocation } from "react-router-dom";
import CreateEventModal from "./CreateEvent";
import { useAuth } from "../auth/AuthContext";
import SearchBar from "./SearchBar";
import { useEvents } from "../contexts/EventContext";
import "./NavBar.css";
import logo from "../assets/townsquare-logo.png";


export default function NavBar() {
  const [openCreate, setOpenCreate] = useState(false);

  const { user, logout, initials } = useAuth();
  const { addEvent } = useEvents();
  const location = useLocation();
  const nav = useNavigate();

  const handleLogout = async () => {
    await logout();
    nav("/login", { replace: true });
  };

  const handleEventCreated = (newEvent) => {
    console.log("NEW EVENT CREATED:", newEvent);
    addEvent(newEvent);
    setOpenCreate(false);

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

          <Link
            to="/profile"
            className="ts-avatar"
            aria-label="Open profile"
            title={user?.displayName || user?.email || "Account"}
          >
            {initials}
          </Link>

          <button
            className="ts-btn ts-btn-ghost"
            onClick={handleLogout}
            aria-label="Log out"
          >
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
