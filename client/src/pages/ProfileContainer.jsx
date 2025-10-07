// src/pages/ProfileContainer.jsx
import React from "react";
import { useAuth } from "../auth/AuthContext";
import ProfilePage from "./Profile"; // your UI component

export default function ProfileContainer() {
  const { user, profile } = useAuth();

  return (
    <ProfilePage
      fullName={profile?.name || user?.displayName || "New User"}
      username={profile?.username || user?.email?.split("@")[0] || "user"}
      friends={profile?.friends ?? 0}
      bio={profile?.bio ?? ""}
      location={profile?.location ?? ""}
      study={profile?.study ?? ""}
      interests={profile?.interests ?? []}
      myEvents={[]}     // TODO: load from your API later
      goingTo={[]}      // TODO: load RSVPs later
    />
  );
}
