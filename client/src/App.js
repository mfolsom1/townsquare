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


function Following() {
  return <h1>Following Page</h1>;
}

function Saved() {
  return <h1>Saved Events Page</h1>;
}

function App() {
  return (
    <AuthProvider>
      <EventProvider>
        <Router>
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
          </Router>
        </EventProvider>
    </AuthProvider>

  );
}

export default App;
