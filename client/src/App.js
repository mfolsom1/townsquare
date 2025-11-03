// App.js: Handles routing
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import NavBar from "./components/NavBar";
import Discover from "./pages/Discover";
import EventDetail from "./pages/EventDetail";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import RequireAuth from "./auth/RequireAuth";
import { AuthProvider } from "./auth/AuthContext";
import { EventProvider } from "./contexts/EventContext";
import ProfileContainer from "./pages/ProfileContainer";
import Profile from "./pages/Profile";
import SavedEventsPage from "./pages/SavedEventsPage";
import Following from "./pages/Following"

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
                    <>
                    <NavBar />
                    <Routes>
                      <Route path="/discover" element={<Discover />} />
                      <Route path="/events/:eventId" element={<EventDetail />} />
                      <Route path="/following" element={<Following />} />
                      <Route path="/saved" element={<SavedEventsPage />} />
                      <Route path="*" element={<Discover />} />
                      <Route path="/profile" element=
                      {<RequireAuth>
                        <ProfileContainer />
                        </RequireAuth>
                      }
                      />
                    </Routes>
                  </>
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
