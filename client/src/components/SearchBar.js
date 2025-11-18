import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import "./SearchBar.css";

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Sync input with URL so back/forward keep the search value
  useEffect(() => {
    setQuery(searchParams.get('q') || '');
  }, [searchParams]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const q = query.trim();

    if (q) {
      navigate(`/discover?q=${encodeURIComponent(q)}`);
    } else {
      navigate('/discover');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="ts-search-form">
      <input
        type="search"
        className="ts-search-input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
        aria-label="Search events"
      />
    </form>
  );
}
