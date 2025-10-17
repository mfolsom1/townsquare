// src/pages/ProfileContainer.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getUserProfile, getUserInterests, verifyUserWithBackend } from "../api";
import ProfilePage from "./Profile";

export default function ProfileContainer() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [interests, setInterests] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;

    async function fetchOrCreate() {
      try {
        if (!user) { navigate("/login", { replace: true }); return; }
        const idToken = await user.getIdToken();

        // 1) try fetch profile
        let p = await getUserProfile(idToken);

        // 2) optional interests endpoint
        let ints = [];
        try { ints = await getUserInterests(idToken); } catch {}

        if (!alive) return;
        setProfile(p);
        setInterests(Array.isArray(ints) ? ints : (p?.interests ?? []));
        setLoading(false);
      } catch (e) {
        // If backend says user doesn't exist yet, create & retry once
        const msg = String(e?.message || "").toLowerCase();
        if (msg.includes("user not found") || msg.includes("404")) {
          try {
            const idToken = await user.getIdToken();
            await verifyUserWithBackend(idToken, {
              // provide minimal data your backend expects
              username: (user?.email || "user").split("@")[0],
              name: user?.displayName || "New User",
              email: user?.email || "",
            });
            // refetch after creation
            if (!alive) return;
            const p = await getUserProfile(idToken);
            let ints = [];
            try { ints = await getUserInterests(idToken); } catch {}
            setProfile(p);
            setInterests(Array.isArray(ints) ? ints : (p?.interests ?? []));
            setLoading(false);
            return;
          } catch (e2) {
            if (!alive) return;
            setError(e2?.message || "Failed to create profile");
            setLoading(false);
            return;
          }
        }
        if (!alive) return;
        setError(e?.message || "Failed to load profile");
        setLoading(false);
      }
    }

    fetchOrCreate();
    return () => { alive = false; };
  }, [user, navigate]);

  if (loading) return <div style={{ padding: 16 }}>Loading profile…</div>;
  if (error)   return <div style={{ padding: 16, color: "#b91c1c" }}>Error: {error}</div>;
  if (!profile) return <div style={{ padding: 16 }}>No profile found.</div>;

  return (
    <ProfilePage
      fullName={profile.name || user?.displayName || "User"}
       username={profile.user?.username}
      friends={profile.friends ?? 0}
      bio={profile.bio || ""}
      location={profile.location || ""}
      study={profile.study || ""}
      interests={interests || []}
      myEvents={[]}
      goingTo={[]}
    />
  );
}
