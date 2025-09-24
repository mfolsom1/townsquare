// App.js: Handles routing
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import Discover from "./pages/Discover";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import RequireAuth from "./auth/RequireAuth";
import { AuthProvider } from "./auth/AuthContext";

function Following() {
  return <h1>Following Page</h1>;
}

function Saved() {
  return <h1>Saved Events Page</h1>;
}

function App() {
  return (
    <AuthProvider>
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
                  <Route path="/following" element={<Following />} />
                  <Route path="/saved" element={<Saved />} />
                  <Route path="*" element={<Discover />} />
                </Routes>
              </>
            </RequireAuth>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
