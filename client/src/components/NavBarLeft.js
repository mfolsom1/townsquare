import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./NavBarLeft.css";

export default function NavBarLeft() {
  const { user } = useAuth();

  // same organization check used by CreateEvent
  const isOrg = Boolean(user && (user.user_type === "organization" || user.is_organization));

  return (
    <nav className="lts-nav">
      <div className="lts-brand"> 
        {/* ...existing brand content... */}
      </div>

      <div className="lts-center">
        {/* Dashboard tab shown first for organizations */}
        {isOrg && (
          <NavLink
            to="/test-org"
            className="lts-tab"
          >
            Dashboard
          </NavLink>
        )}

        <NavLink to="/discover" className="lts-tab">Discover</NavLink>
        <NavLink to="/following" className="lts-tab">Following</NavLink>
        <NavLink to="/saved" className="lts-tab">Saved Events</NavLink>
      </div>

      {/* ...existing right / footer markup (create button, avatar, etc.) ... */}
    </nav>
  );
}
