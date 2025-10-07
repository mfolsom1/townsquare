import React, { createContext, useContext, useEffect, useState,} from "react";
import { auth, db } from "../firebase";
import {
  onAuthStateChanged,
  signOut,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  updateProfile,
} from "firebase/auth";
// ADDED: firestore
import {
  doc, setDoc, onSnapshot, serverTimestamp, runTransaction
} from "firebase/firestore";

const AuthContext = createContext(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}


// Small helper to compute “initials” for avatars, etc.
const initialsFrom = (name, email) =>
  (name?.trim() || email || "U")
    .split(/\s+/)
    .map((s) => s[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();


// provider component wraps app
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);   // Firestore profile
  const [loading, setLoading] = useState(true);

  // CHANGED: watch auth state, then watch profile doc if signed in 
  useEffect(() => {
    setLoading(true);
    const unsubAuth = onAuthStateChanged(auth, (u) => {
      setUser(u || null);
      // Do not set loading=false here; if we are signed in,
      // we wait for the profile snapshot below to resolve first.
      if (!u) setLoading(false);
    });
    return () => unsubAuth();
  }, []);

  // CHANGED: When signed in, sub to users/uid to stream profile changes
    useEffect(() => {
    if (!user) {
      // Signed out: clear profile and ensure loading is false.
      setProfile(null);
      setLoading(false);
      return;
    }

    const ref = doc(db, "users", user.uid);
    const unsub = onSnapshot(
      ref,
      (snap) => {
        setProfile(snap.exists() ? snap.data() : null);
        setLoading(false);
      },
      // On error, don’t lock the app—consider logging if you have Sentry etc.
      () => setLoading(false)
    );

    return () => unsub();
  }, [user]);

  // CHANGED: Resserve unqiue user automatically 
  async function reserveUsernameTx(username, uid) {
    const handle = (username || "").trim().toLowerCase();
    if (!handle) throw new Error("Username is required.");

    const handleRef = doc(db, "usernames", handle);
    const userRef = doc(db, "users", uid);

    await runTransaction(db, async (tx) => {
      const taken = await tx.get(handleRef);
      if (taken.exists()) {
        throw new Error("That username is taken.");
      }
      tx.set(handleRef, { uid });
      tx.set(userRef, { username: handle }, { merge: true });
    });

    return handle;
  }
  // Signup flow:
  // Create auth user -> update displayname -> reserve username -> seed users/uid with prof fields
  async function signup({ name, username, email, password }) {
  const displayName = (name || "").trim();

// Create the auth user
  const cred = await createUserWithEmailAndPassword(auth, email, password);

    // Attach display name to the auth user (optional but nice)
    if (displayName) {
      await updateProfile(cred.user, { displayName });
    }

    // Reserve username + set it on the profile doc
    const uid = cred.user.uid;
    const handle = await reserveUsernameTx(username, uid);

    // Seed the profile document
    await setDoc(
      doc(db, "users", uid),
      {
        uid,
        name: displayName || cred.user.displayName || "",
        username: handle, // guaranteed unique by the transaction above
        email,
        friends: 0,
        bio: "",
        location: "",
        study: "",
        interests: [],
        createdAt: serverTimestamp(),
      },
      { merge: true } // idempotent in case we retry
    );

    return cred.user;
  }

  // 5) Email/password login + logout
  const login = (email, password) =>
    signInWithEmailAndPassword(auth, email, password);

  const logout = () => signOut(auth);

  // 6) Derived helpers exposed to the app
  const value = {
      user,            // Firebase Auth user (or null)
      profile,         // Firestore profile (or null)
      loading,         // true while resolving auth/profile
      signup,          // create account + profile + username reservation
      login,           // sign in with email/password
      logout,          // sign out
      initials: initialsFrom(profile?.name || user?.displayName, user?.email),
  };

  // Don’t render children until we know the auth state (prevents UI flicker)
  if (loading) return null;

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

