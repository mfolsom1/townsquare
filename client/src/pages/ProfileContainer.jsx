import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import {
  getUserProfile,
  getUserInterests,
  verifyUserWithBackend,
  updateUserProfile,
  getUserOrganizedEvents,
  getUserAttendingEvents,
} from "../api";
import { updateProfile as fbUpdateProfile } from "firebase/auth";
import ProfilePage from "./Profile";

// helper: pick first non-empty string
const pick = (...cands) => cands.find(v => typeof v === "string" && v.trim().length) || "";

// Normalize whatever the backend returns into stable props for the UI.
function normalizeProfile(p, fbUser) {
  const top = p || {};
  const nested = top.user || {};

  const name = pick(
    top.name, top.displayName, top.fullName,
    nested.name, nested.displayName, nested.fullName,
    fbUser?.displayName
  );

  const username = pick(top.username, nested.username);
  const bio = pick(top.bio, nested.bio);
  const location = pick(top.location, nested.location);

  const friends = Number.isFinite(top.friends) ? top.friends : 0;
  const interests = Array.isArray(top.interests) ? top.interests : [];

  return { name, username, bio, location, friends, interests };
}

export default function ProfileContainer() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [interests, setInterests] = useState([]);
  const [myEvents, setMyEvents] = useState([]);
  const [attendingEvents, setAttendingEvents] = useState([]);
  const [error, setError] = useState(null);

  // Helper function to format event data for the UI
  const formatEventForUI = (event) => ({
    title: event.title,
    date: event.start_time ? new Date(event.start_time).toLocaleDateString() : 'TBD',
    location: event.location,
    id: event.event_id,
    imageUrl: event.image_url
  });

  async function loadProfile(idToken) {
    const rawProfile = await getUserProfile(idToken);
    const norm = normalizeProfile(rawProfile, user);
    let ints = [];
    let myEvts = [];
    let attendingEvts = [];

    try {
      const rawInts = await getUserInterests(idToken);
      ints = Array.isArray(rawInts) ? rawInts : rawInts?.interests ?? norm.interests ?? [];
    } catch {
      ints = norm.interests ?? [];
    }

    try {
      const organizedEventsResponse = await getUserOrganizedEvents(idToken);
      const organizedEvents = organizedEventsResponse?.events || [];
      myEvts = organizedEvents.map(formatEventForUI);
    } catch (e) {
      console.warn("Failed to fetch organized events:", e);
      myEvts = [];
    }

    try {
      const attendingEventsResponse = await getUserAttendingEvents(idToken);
      const attendingEventsData = attendingEventsResponse?.events || [];
      attendingEvts = attendingEventsData.map(formatEventForUI);
    } catch (e) {
      console.warn("Failed to fetch attending events:", e);
      attendingEvts = [];
    }

    setProfile(rawProfile);
    setInterests(ints);
    setMyEvents(myEvts);
    setAttendingEvents(attendingEvts);
    return { rawProfile, norm, ints, myEvts, attendingEvts };
  }

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        if (!user) { navigate("/login", { replace: true }); return; }
        setLoading(true);
        const idToken = await user.getIdToken();

        try {
          await loadProfile(idToken);
          if (!alive) return;
          setLoading(false);
        } catch (e) {
          const msg = String(e?.message || "").toLowerCase();
          if (msg.includes("user not found") || msg.includes("404")) {
            await verifyUserWithBackend(idToken, {
              username: (user?.email || "user").split("@")[0],
              name: user?.displayName || "New User",
              email: user?.email || "",
            });
            if (!alive) return;
            await loadProfile(idToken);
            if (!alive) return;
            setLoading(false);
          } else {
            throw e;
          }
        }
      } catch (e) {
        if (!alive) return;
        setError(e?.message || "Failed to load profile");
        setLoading(false);
      }
    })();

    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, navigate]); // loadProfile is called within async IIFE, not directly as dependency

  // Persist edits, sync Firebase displayName, then refetch so refresh shows the new value
  const onSaveProfile = async ({ fullName, username, bio, location }) => {
    const idToken = await user.getIdToken();

    // 1) Save to your backend — send ALL common aliases so the server updates the right field.
    await updateUserProfile(idToken, {
      name: fullName,
      displayName: fullName,
      fullName,
      username,
      bio,
      location,
    });

    // 2) Keep Firebase Auth in sync (so any fallback/other UI sees the new name)
    try {
      await fbUpdateProfile(user, { displayName: fullName });
      // optional: await user.reload();
    } catch (e) {
      // non-fatal; backend is still updated
      console.warn("Failed to update Firebase displayName:", e);
    }

    // 3) Refetch canonical profile from backend
    const { norm } = await loadProfile(idToken);

    return {
      fullName: norm.name,
      username: norm.username,
      bio: norm.bio,
      location: norm.location,
    };
  };

  if (loading) return <div style={{ padding: 16 }}>Loading profile…</div>;
  if (error) return <div style={{ padding: 16, color: "#b91c1c" }}>Error: {error}</div>;

  const norm = normalizeProfile(profile, user);

  return (
    <ProfilePage
      fullName={norm.name || "User"}
      username={norm.username || ""}
      friends={norm.friends ?? 0}
      bio={norm.bio || ""}
      location={norm.location || ""}
      study={profile?.study || ""}
      interests={interests || []}
      myEvents={myEvents || []}
      goingTo={attendingEvents || []}
      onSaveProfile={onSaveProfile}
      onCreateEvent={() => { }}
    />
  );
}
