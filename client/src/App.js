// App.js: Handles routing
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import NavBar from "./components/NavBar";
import NavBarLeft from "./components/NavBarLeft";
import Discover from "./pages/Discover";
import EventDetail from "./pages/EventDetail";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import RequireAuth from "./auth/RequireAuth";
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
                    <NavBarLeft />

                    <div style={{ flex: 1, padding: "20px" }}>
                      <Routes>
                        <Route path="/discover" element={<Discover />} />
                        <Route path="/events/:eventId" element={<EventDetail />} />
                        <Route path="/following" element={<Following />} />
                        <Route path="/saved" element={<SavedEventsPage />} />
                        {/* TEMPORARY LINK TO ORG-DASH */}
                        <Route
                          path="/dashboard"
                          element={
                            <>
                              <OrgDashboardContainer />
                            </>
                          }
                        />
                        <Route path="*" element={<Discover />} />
                        <Route
                          path="/profile"
                          element={
                            <RequireAuth>
                              <ProfileContainer />
                            </RequireAuth>
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
