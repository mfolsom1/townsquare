
import React, { useEffect, useState } from 'react';
import { getUserInterests, setUserInterests } from '../api';
import { useAuth } from '../auth/AuthContext';


const UpdateInterests = () => {
  const { user } = useAuth();
  const [idToken, setIdToken] = useState(null);
  const [interests, setInterests] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (user) {
      user.getIdToken().then(setIdToken);
    }
  }, [user]);

  useEffect(() => {
    const fetchInterests = async () => {
      setLoading(true);
      setMessage('');
      try {
        const userInterests = await getUserInterests(idToken);
        setInterests(userInterests.join(', '));
      } catch (err) {
        setMessage('Failed to load interests.');
      } finally {
        setLoading(false);
      }
    };
    if (idToken) fetchInterests();
  }, [idToken]);

  const handleChange = (e) => {
    setInterests(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    const interestsArray = interests
      .split(',')
      .map((i) => i.trim())
      .filter((i) => i.length > 0);
    try {
      await setUserInterests(idToken, interestsArray);
      setMessage('Interests updated successfully!');
    } catch (err) {
      setMessage('Failed to update interests.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="update-interests-page">
      <h2>Update Your Interests</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="interests">Interests (comma-separated):</label>
        <input
          id="interests"
          type="text"
          value={interests}
          onChange={handleChange}
          disabled={loading}
          style={{ width: '100%', marginBottom: '1em' }}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Updating...' : 'Update Interests'}
        </button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
};

export default UpdateInterests;
