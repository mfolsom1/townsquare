
/* simple email/password login. redirects to disover page */

import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./Auth.css";

export default function Login() {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [err, setErr] = useState("");
  const nav = useNavigate();
  const location = useLocation();
  // if user came from protected route, redirect back
  // otherwise go to disover page
  const redirectTo = location.state?.from?.pathname || "/discover";

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    // attempt login 
    try {
      await login(form.email, form.password);
      nav(redirectTo, { replace: true });
    } catch (e) {
        // error msg if wrong login
      setErr(e.message);
    }
  };

  return (
    <main className="auth-wrap">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Welcome back</h1>
        {err && <div className="auth-error">{err}</div>}
        <label>
          Email
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </label>
        <button className="auth-btn primary" type="submit">Log in</button>
        <p className="auth-switch">
          New here? <Link to="/signup">Create an account</Link>
        </p>
      </form>
    </main>
  );
}
