import React, { useState } from "react";
import { NavLink, Link } from "react-router-dom";
import CreateEventModal from "./CreateEvent";
import "./NavBar.css";

export default function NavBar({ initials = "N/A" }) { // TODO: replace with user initials
  const [openCreate, setOpenCreate] = useState(false); // if modal is open

  return (
    <>
      <header className="ts-nav">
        <div className="ts-left">
          <Link to="/discover" className="ts-brand">Townsquare</Link>
        </div>

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
          <Link to="/account" className="ts-avatar" title="Account Profile">
            {initials}
          </Link>
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
