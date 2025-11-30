import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { getUserInterests } from '../api';

/**
 * Component that checks if user has set up interests.
 * If not, redirects to interests page.
 * If yes, renders children.
 */
export default function RequireInterests({ children }) {
  const { user, isNewUser, setIsNewUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [hasInterests, setHasInterests] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    async function checkInterests() {
      if (!user) {
        setLoading(false);
        return;
      }

      // If user just signed up, redirect to interests immediately
      if (isNewUser) {
        navigate('/interests', { replace: true });
        return;
      }

      try {
        const idToken = await user.getIdToken();
        const res = await getUserInterests(idToken);
        
        // Check if the response indicates interests have been set up
        // This includes both cases: user has interests OR user explicitly skipped (empty array was saved)
        if (res && res.hasOwnProperty('interests')) {
          // User has completed the interests setup (either selected some or skipped)
          setHasInterests(true);
        } else {
          // User has not completed interests setup at all, redirect to interests page
          navigate('/interests', { replace: true });
        }
      } catch (err) {
        console.error('Failed to check user interests:', err);
        // On error, assume they need to set interests
        navigate('/interests', { replace: true });
      } finally {
        setLoading(false);
      }
    }

    checkInterests();
  }, [user, isNewUser, navigate]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!hasInterests && !isNewUser) {
    return null; // Will redirect
  }

  return children;
}