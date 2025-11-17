import React from "react";
import { NavLink } from "react-router-dom";
import "./NavBarLeft.css";

export default function NavBarLeft() {


  return (
    <nav className="lts-nav">
      <div className="lts-brand"> 
        {/* ...existing brand content... */}
      </div>

      <div className="lts-center">
        <NavLink to="/discover" className="lts-tab">Discover</NavLink>
        <NavLink to="/following" className="lts-tab">Following</NavLink>
        <NavLink to="/saved" className="lts-tab">Saved Events</NavLink>
      </div>

      {/* ...existing right / footer markup (create button, avatar, etc.) ... */}
    </nav>
  );
}
