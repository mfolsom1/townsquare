import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext"; 
import "./Auth.css"; 

export default function Signup() {
    //TODO: implement stronger password requirements 
    
    // get signup function from AuthContext
    const { signup } = useAuth();

    // local state to manage form inputs
    const [form, setForm] = useState({ name: "", email: "", password: "" });

    // local state to track and display error messages
    const [err, setErr] = useState("");

    // navigation + redirect handling
    const nav = useNavigate();
    const location = useLocation();

    // determine where to send user after signup -> discover page
    const redirectTo = location.state?.from?.pathname || "/discover";

    // handle form submission
    const onSubmit = async (e) => {
        e.preventDefault(); // stop page refresh
        setErr("");         // clear previous error
        try {
        // call signup function
        await signup(form);

        // redirect to intended page or `/discover`
        nav(redirectTo, { replace: true });
        } catch (e) {
        // show error if signup fails
        setErr(e.message);
        }
    };

    return (
        <main className="auth-wrap">
        <form className="auth-card" onSubmit={onSubmit}>
            <h1>Create your account</h1>

            {/* Error message (only shown if signup fails) */}
            {err && <div className="auth-error">{err}</div>}

            {/* Name field */}
            <label>
            Name
            <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="First Last"
                required
            />
            </label>

            {/* email field */}
            <label>
            Email
            <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
            />
            </label>

            {/* password field */}
            <label>
            Password
            <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                minLength={6} // basic password length requirement for firebase 
                required
            />
            </label>

            {/* signup button */}
            <button className="auth-btn primary" type="submit">
            Sign up
            </button>

            {/* link to login page if user already has an account */}
            <p className="auth-switch">
            Already have an account? <Link to="/login">Log in</Link>
            </p>
        </form>
        </main>
    );
    }
