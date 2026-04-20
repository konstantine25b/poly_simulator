import { useState } from "react";

function validateInputs(email, password, minPasswordLength) {
  if (!email) return "Please enter your email.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Please enter a valid email address.";
  if (!password) return "Please enter your password.";
  if (password.length < minPasswordLength) {
    return `Password must be at least ${minPasswordLength} characters.`;
  }
  return null;
}

export function AuthForm({ submitLabel, onSubmit, minPasswordLength = 1, passwordHint }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (busy) return;
    const cleanEmail = email.trim();
    const localErr = validateInputs(cleanEmail, password, minPasswordLength);
    if (localErr) {
      setErr(localErr);
      return;
    }
    setErr(null);
    setBusy(true);
    try {
      await onSubmit(cleanEmail, password);
    } catch (ex) {
      setErr(ex.message || String(ex));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <div className="auth-field">
        <label className="auth-label" htmlFor="auth-email">
          Email
        </label>
        <input
          id="auth-email"
          className="auth-input"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div className="auth-field">
        <label className="auth-label" htmlFor="auth-password">
          Password
        </label>
        <input
          id="auth-password"
          className="auth-input"
          type="password"
          autoComplete={submitLabel === "Create account" ? "new-password" : "current-password"}
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={minPasswordLength}
          required
        />
        {passwordHint ? <span className="auth-hint">{passwordHint}</span> : null}
      </div>
      {err ? <p className="auth-error">{err}</p> : null}
      <button className="auth-submit" type="submit" disabled={busy}>
        {busy ? "Please wait…" : submitLabel}
      </button>
    </form>
  );
}
