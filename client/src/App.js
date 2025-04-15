// App.js: Handles routing
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Discover from './pages/Discover';

function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Discover />} />
      </Routes>
    </Router>
  );
}

export default App;