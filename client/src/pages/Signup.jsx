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

    // navigation + redirect handling
    const nav = useNavigate();
    const location = useLocation();

    // determine where to send user after signup -> discover page
    const redirectTo = location.state?.from?.pathname || "/discover";

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

        // check password strength
        if (!isStrongPassword) {
            setErr("Password must be at least 8 characters and include an uppercase letter, a number, and a special character.");
            return;
        }

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
