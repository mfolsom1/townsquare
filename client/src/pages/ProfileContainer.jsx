import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import {
  getUserProfile,
  getUserInterests,
  verifyUserWithBackend,
  updateUserProfile,
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
  const [error, setError] = useState(null);

  async function loadProfile(idToken) {
    const rawProfile = await getUserProfile(idToken);
    const norm = normalizeProfile(rawProfile, user);
    let ints = [];
    try {
      const rawInts = await getUserInterests(idToken);
      ints = Array.isArray(rawInts) ? rawInts : rawInts?.interests ?? norm.interests ?? [];
    } catch {
      ints = norm.interests ?? [];
    }
    setProfile(rawProfile);
    setInterests(ints);
    return { rawProfile, norm, ints };
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
  }, [user, navigate]);

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
  if (error)   return <div style={{ padding: 16, color: "#b91c1c" }}>Error: {error}</div>;

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
      myEvents={[]}
      goingTo={[]}
      onSaveProfile={onSaveProfile}
      onCreateEvent={() => {}}
    />
  );
}
