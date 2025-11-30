import React, { useState, useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./Style.css";
import "./Auth.css";


export default function Signup() {

    // get signup function from AuthContext
    const { signup } = useAuth();

    // local state to manage form inputs
    const [form, setForm] = useState({ name: "", username: "", email: "", password: "", userType: "", organizationName: "", });

    // local state to track and display error messages
    const [err, setErr] = useState("");

    // navigation + redirect handling
    const nav = useNavigate();
    const location = useLocation();

    // determine where to send user after signup -> interests page for new users
    const redirectTo = location.state?.from?.pathname || "/interests";

    // password validation function 
    const isStrongPassword = useMemo(() => {
        const pwd = (form.password ?? "").trim();
        const minLength = pwd.length >= 8;
        const hasUpper = /[A-Z]/.test(pwd);
        const hasNumber = /[0-9]/.test(pwd);
        const hasSpecial = /[^A-Za-z0-9]/.test(pwd);
        return minLength && hasUpper && hasNumber && hasSpecial;
    }, [form.password]);

    // username validation function
    const isValidUsername = useMemo(() => {
        const username = (form.username ?? "").trim();
        const minLength = username.length >= 3;
        const maxLength = username.length <= 20;
        const validChars = /^[a-zA-Z0-9_-]+$/.test(username); // Only letters, numbers, underscores, and hyphens
        return minLength && maxLength && validChars;
    }, [form.username]);

    const isIndividual = form.userType === "individual";  
    const isOrg = form.userType === "organization";


    // handle form submission
    const onSubmit = async (e) => {
        e.preventDefault(); // stop page refresh
        setErr("");         // clear previous error

        // choose acc type first
        if (!form.userType) {
            setErr("Please select an account type.");
            return;
        }

        // validate required fields
        if (!form.username.trim()) {
            setErr("Username is required.");
            return;
        }

        if (!isValidUsername) {
            setErr("Username must be 3-20 characters and contain only letters, numbers, underscores, and hyphens.");
            return;
        }

        // individual: name required
        if (isIndividual && !form.name.trim()) {
            setErr("Name is required for individual accounts.");
            return;
        }

        // org: organization name required
        if (isOrg && !form.organizationName.trim()) {
            setErr("Organization name is required for organization accounts.");
            return;
        }

        // check password strength
        if (!isStrongPassword) {
            setErr("Password must be at least 8 characters and include an uppercase letter, a number, and a special character.");
            return;
        }
        // validate organization requirements
        if (form.userType === "organization" && !form.organizationName.trim()) {
            setErr("Organization name is required for organization accounts.");
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

    const canSubmit =
    !!form.userType &&
    isStrongPassword &&
    isValidUsername &&
    form.email.trim() &&
    ((isIndividual && form.name.trim()) ||
      (isOrg && form.organizationName.trim()));

    return (
        <main className="auth-wrap">
            <form className="auth-card" onSubmit={onSubmit}>
                <h2 className="auth-title">Townsquare</h2>
                <h1>Create your account</h1>

                {/* error message (only shown if signup fails) */}
                {err && <div className="auth-error">{err}</div>}

                {/* account type shown first, alone */}
        <div className="auth-section">
          <label className="auth-label">Account type</label>
          <div className="account-type-toggle">
            <button
              type="button"
              className={
                isIndividual ? "account-type-pill active" : "account-type-pill"
              }
              onClick={() =>
                setForm((prev) => ({
                  ...prev,
                  userType: "individual",
                }))
              }
            >
              Individual
            </button>
            <button
              type="button"
              className={isOrg ? "account-type-pill active" : "account-type-pill"}
              onClick={() =>
                setForm((prev) => ({
                  ...prev,
                  userType: "organization",
                }))
              }
            >
              Organization
            </button>
          </div>
        </div>

        {/* If no account type chosen yet, stop here */}
        {!form.userType && (
          <p className="auth-hint">
            Select an account type above to continue.
          </p>
        )}

        {/* Individual-specific: Name field (same as before) */}
        {isIndividual && (
          <label>
            Name
            <input
              value={form.name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="First Last"
              required
            />
          </label>
        )}

        {/* Organization-specific: Organization name field */}
        {isOrg && (
          <label>
            Organization name
            <input
              value={form.organizationName}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  organizationName: e.target.value,
                }))
              }
              placeholder="Ex: Gator Coding Club"
              required
            />
          </label>
        )}

        {/* Shared fields: only show after type is chosen */}
        {form.userType && (
          <>
            {/* Username (same logic as before) */}
            <label>
              Username
              <div className="input-wrapper">
                <input
                  value={form.username}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, username: e.target.value }))
                  }
                  placeholder="Pick a unique username"
                  required
                  className={
                    form.username
                      ? isValidUsername
                        ? "valid-input"
                        : "invalid-input"
                      : ""
                  }
                  aria-invalid={
                    form.username && !isValidUsername ? "true" : "false"
                  }
                />
                {form.username &&
                  (isValidUsername ? (
                    <span className="icon valid">✔</span>
                  ) : (
                    <span className="icon invalid">!</span>
                  ))}
              </div>
              {form.username && !isValidUsername && (
                <small className="auth-hint">
                  Username must be 3-20 characters and contain only letters,
                  numbers, underscores, and hyphens.
                </small>
              )}
            </label>

            {/* Email */}
            <label>
              Email
              <input
                type="email"
                value={form.email}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, email: e.target.value }))
                }
                required
              />
            </label>

            {/* Password (same validation as before) */}
            <label>
              Password
              <div className="input-wrapper">
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, password: e.target.value }))
                  }
                  required
                  className={
                    form.password
                      ? isStrongPassword
                        ? "valid-input"
                        : "invalid-input"
                      : ""
                  }
                  aria-invalid={
                    form.password && !isStrongPassword ? "true" : "false"
                  }
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
                  Password must be at least 8 characters and include an
                  uppercase letter, a number, and a special character.
                </small>
              )}
            </label>
          </>
        )}

        <button
          className="auth-btn primary"
          type="submit"
          disabled={!canSubmit}
        >
          Sign up
        </button>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </main>
  );
}