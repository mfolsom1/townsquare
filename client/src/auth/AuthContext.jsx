import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { auth } from "../firebase";
import {
  onAuthStateChanged,
  signOut,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  updateProfile,
} from "firebase/auth";

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
      signup: async ({ name, email, password }) => {
        const cred = await createUserWithEmailAndPassword(auth, email, password);
        if (name) await updateProfile(cred.user, { displayName: name });
        return cred.user;
      },
      // email/pass login
      login: (email, password) => signInWithEmailAndPassword(auth, email, password),
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
