// App.js: Handles routing
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import NavBar from "./components/NavBar";
import Discover from "./pages/Discover";
import EventDetail from "./pages/EventDetail";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Interests from "./pages/Interests";
import RequireAuth from "./auth/RequireAuth";
import RequireInterests from "./auth/RequireInterests";
import { AuthProvider } from "./auth/AuthContext";
import { EventProvider } from "./contexts/EventContext";
import ProfileContainer from "./pages/ProfileContainer";
import SavedEventsPage from "./pages/SavedEventsPage";
import Following from "./pages/Following"
import OrgDashboardContainer from "./pages/OrgDashboardContainer";

function App() {
  return (
    <Router>
      <AuthProvider>
        <EventProvider>
          <Routes>

            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route
              path="/*"
              element={
                <RequireAuth>
                  <NavBar />

                  <div style={{ display: "flex" }}>


                    <div style={{ flex: 1, padding: "20px" }}>
                      <Routes>
                        <Route path="/interests" element={<Interests />} />
                        <Route path="/discover" element={<RequireInterests><Discover /></RequireInterests>} />
                        <Route path="/events/:eventId" element={<RequireInterests><EventDetail /></RequireInterests>} />
                        <Route path="/following" element={<RequireInterests><Following /></RequireInterests>} />
                        <Route path="/saved" element={<RequireInterests><SavedEventsPage /></RequireInterests>} />
                        {/* TEMPORARY LINK TO ORG-DASH */}
                        <Route
                          path="/dashboard"
                          element={
                            <RequireInterests>
                              <OrgDashboardContainer />
                            </RequireInterests>
                          }
                        />
                        <Route path="*" element={<RequireInterests><Discover /></RequireInterests>} />
                        <Route
                          path="/profile"
                          element={
                            <RequireInterests>
                              <ProfileContainer />
                            </RequireInterests>
                          }
                        />
                      </Routes>
                    </div>
                  </div>
                </RequireAuth>
              }
            />
          </Routes>
        </EventProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
