
import React from "react";
import OrgDashboard from "./OrgDashboard";

// mock org object (what the backend will eventually return)
const mockOrg = {
  name: "Umbrella Corp",
  handle: "@umbrella",
  email: "email@example.com",
  location: "Gainesville, FL",
  followers: 8,
  about: "Welcome to Umbrella Corporation.",
  tags: ["Arts", "Music", "Tech"],
  bannerUrl: "",
  avatarUrl: null,
};

// mock events
const mockEvents = [];

export default function OrgDashboardContainer() {
  return (
    <OrgDashboard
      events={mockEvents}
      initialOrg={mockOrg}
      onSaveOrgProfile={(d) => Promise.resolve(d)} 
      onCreateEvent={() => {}}
    />
  );
}
