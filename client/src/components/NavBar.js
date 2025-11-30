import React, { useState, useEffect } from "react";
import { NavLink, Link, useNavigate, useLocation } from "react-router-dom";
import CreateEventModal from "./CreateEvent";
import { useAuth } from "../auth/AuthContext";
import SearchBar from "./SearchBar";
import { useEvents } from "../contexts/EventContext";
import { getUserProfile } from "../api";
import "./NavBar.css";
import logo from "../assets/townsquare-logo.png";


export default function NavBar() {
  const [openCreate, setOpenCreate] = useState(false);

  const { user, initials } = useAuth();
  const [userProfile, setUserProfile] = useState(null);
  const { addEvent } = useEvents();
  const location = useLocation();
  const nav = useNavigate();

  const isOrganization = userProfile?.user_type === 'organization';

  useEffect(() => {
    let cancelled = false;
    async function loadUserProfile() {
      if (!user) return;
      try {
        const idToken = await user.getIdToken();
        const response = await getUserProfile(idToken);
        if (!cancelled) {
          setUserProfile(response?.user || null);
        }
      } catch (e) {
        if (!cancelled) {
          console.error("Failed to load user profile:", e);
          setUserProfile(null);
        }
      }
    }
    loadUserProfile();
    return () => { cancelled = true; };
  }, [user]);

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
          <NavLink to="/interests" className="ts-tab">
            Interests
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