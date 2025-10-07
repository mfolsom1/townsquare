// Private-route wrapper 
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return null;            // or a spinner
  return user ? children : <Navigate to="/login" replace state={{ from: loc }} />;
}
