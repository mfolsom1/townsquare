import React, { useState } from "react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import CreateEventModal from "./CreateEvent";
import { useAuth } from "../auth/AuthContext";
import SearchBar from "./SearchBar";
import "./NavBar.css";

export default function NavBar() { 
  // create event modal is only visible to users
  const [openCreate, setOpenCreate] = useState (false);

  const { user, logout, initials } = useAuth();

  // redirect after logout
  const nav = useNavigate();
  
  // redirect to /login if logging out
  const handleLogout = async () => {
    await logout();
    nav("/login", { replace: true })
  }

  return (
    <>
      <header className="ts-nav">
        <div className="ts-left">
          <Link to="/discover" className="ts-brand">Townsquare</Link>
        </div>

        <SearchBar />

        <nav className="ts-center">
          <NavLink to="/discover" className="ts-tab">Discover</NavLink>
          <NavLink to="/following" className="ts-tab">Following</NavLink>
          <NavLink to="/saved" className="ts-tab">Saved Events</NavLink>
        </nav>

        <div className="ts-right">
          <button className="ts-create-btn" onClick={() => setOpenCreate(true)}>
            Create Event +
          </button>

          {/* avatar links to account profile */}
          <Link to="/profile" className="ts-avatar" aria-label="Open profile" title={user?.displayName || user?.email || "Account"}>
            {initials}
          </Link>

          <button className="ts-logout" onClick={handleLogout} aria-label="Log out">
            Log out
          </button>
        </div>
      </header>

      <CreateEventModal
        open={openCreate}
        onClose={() => setOpenCreate(false)}
        onCreate={(data) => console.log("NEW EVENT:", data)}
      />
    </>
  );
}
