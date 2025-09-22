// App.js: Handles routing
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import Discover from "./pages/Discover";

function Following() {
  return <h1>Following Page</h1>;
}

function Saved() {
  return <h1>Saved Events Page</h1>;
}

function App() {
  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/discover" element={<Discover />} />
        <Route path="/following" element={<Following />} />
        <Route path="/saved" element={<Saved />} />
        <Route path="*" element={<Discover />} />
      </Routes>
    </Router>
  );
}

export default App;
