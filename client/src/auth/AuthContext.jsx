import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { auth } from "../firebase";
import {
  onAuthStateChanged,
  signOut,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  updateProfile,
} from "firebase/auth";
import { verifyUserWithBackend } from "../api";

const AuthContext = createContext(null);

// provider component wraps app
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  // run once to sub to auth state
  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setReady(true);
    });
    return unsub;
  }, []);

  const value = useMemo(
    () => ({
      user,
      signup: async ({ name, username, email, password }) => {
        // Validate that username is provided
        if (!username || username.trim().length === 0) {
          throw new Error("Username is required");
        }
        
        console.log("Signup attempt with:", { name, username, email }); // Debug log
        
        // Create user in Firebase
        const cred = await createUserWithEmailAndPassword(auth, email, password);
        
        // Update the user's display name in Firebase if provided
        if (name) await updateProfile(cred.user, { displayName: name });
        
        // Get the ID token to authenticate with backend
        const idToken = await cred.user.getIdToken();
        
        // Prepare additional user data for backend
        const userData = {
          username: username.trim(),
          name: name
        };
        
        console.log("Sending to backend:", userData); // Debug log
        
        // Create/verify user in backend database
        await verifyUserWithBackend(idToken, userData);
        
        return cred.user;
      },
      // email/pass login
      login: async (email, password) => {
        const cred = await signInWithEmailAndPassword(auth, email, password);
        
        // Get the ID token and verify with backend
        const idToken = await cred.user.getIdToken();
        await verifyUserWithBackend(idToken);
        
        return cred.user;
      },
      //logout current user
      logout: () => signOut(auth),
      initials: user?.displayName
        ? user.displayName
            .split(" ")
            .map((s) => s[0])
            .join("")
            .toUpperCase()
        : (user?.email?.[0] ?? "N").toUpperCase(),
    }),
    [user]
  );

  // avoid flash-of-unauthenticated by waiting until firebase resolves
  if (!ready) return null;

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
