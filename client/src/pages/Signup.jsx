import React, { useState, useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext"; 
import "./Auth.css"; 

export default function Signup() {

    // get signup function from AuthContext
    const { signup } = useAuth();

    // local state to manage form inputs
    const [form, setForm] = useState({ name: "", username: "", email: "", password: "" });

    // local state to track and display error messages
    const [err, setErr] = useState("");
    // ADDED: gaurd double submit
    const [pending, setPending] = useState(false);            

    // navigation + redirect handling
    const nav = useNavigate();
    const location = useLocation();

    // determine where to send user after signup -> discover page
    const redirectTo = location.state?.from?.pathname || "/discover";

    // CHANGED: Username policy (a–z, 0–9, underscore, 3–20)
    const normalizedUsername = useMemo(
        () => form.username.trim().toLowerCase(),
        [form.username]
    );
    const isValidUsername = useMemo(
        () => /^[a-z0-9_]{3,20}$/.test(normalizedUsername),
        [normalizedUsername]
    );

    // password validation function 
    const isStrongPassword = useMemo(() => {
        const pwd = (form.password ?? "").trim();           
        const minLength = pwd.length >= 8;                    
        const hasUpper   = /[A-Z]/.test(pwd);                 
        const hasNumber  = /[0-9]/.test(pwd);                  
        const hasSpecial = /[^A-Za-z0-9]/.test(pwd);           
    return minLength && hasUpper && hasNumber && hasSpecial; 
    }, [form.password]);  


    // handle form submission
    const onSubmit = async (e) => {
        e.preventDefault(); // stop page refresh
        setErr("");         // clear previous error

        // check username validity 
        if (!isValidUsername) {
            setErr("Username must be 3–20 chars, a–z, 0–9, or underscore.");
            return;
        }

        // check password strength
        if (!isStrongPassword) {
            setErr("Password must be at least 8 characters and include an uppercase letter, a number, and a special character.");
            return;
        }

        try {
        // call signup function
        setPending(true);
        // ADDED: send normalized username + trimmed name
        await signup({
            name: form.name.trim(),
            username: normalizedUsername,
            email: form.email.trim(),
            password: form.password, 
        });

        // redirect to intended page or `/discover`
        nav(redirectTo, { replace: true });
        } catch (e) {
        // show error if signup fails
        const msg =
            e?.message?.includes("username is taken")
            ? "That username is taken. Please choose another."
            : e?.message || "Could not sign up. Please try again.";
        setErr(msg);
        } finally {
        setPending(false);                                
        }
    };

    return (
        <main className="auth-wrap">
        <form className="auth-card" onSubmit={onSubmit}>
            <h1>Create your account</h1>

            {/* error message (only shown if signup fails) */}
            {err && <div className="auth-error">{err}</div>}

            {/* name field */}
            <label>
            Name
            <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="First Last"
                required
            />
            </label>
            
            {/*username field */}
            <label>
                Username
                <input
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                placeholder="Pick a unique username"
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
            <div className="input-wrapper"> 
                <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                className={
                    form.password
                    ? isStrongPassword
                        ? "valid-input"
                        : "invalid-input"
                    : ""
                }
                aria-invalid={form.password && !isStrongPassword ? "true" : "false"}
                />
                {form.password &&
                (isStrongPassword ? (
                    <span className="icon valid">✔</span>
                ) : (
                    <span className="icon invalid">!</span>
                ))}
            </div> 

            {form.password && !isStrongPassword && (                
                <small className="auth-hint">                       
                Password must be at least 8 characters and include an uppercase letter, a number, and a special character. {/* ADDED */}
                </small>                                          
            )}                                                    
            </label>

            {/* disable submit until strong */}
            <button className="auth-btn primary" type="submit" disabled={!isStrongPassword}>
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
