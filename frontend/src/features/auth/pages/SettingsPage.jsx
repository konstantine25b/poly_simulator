import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useBrandLogo } from "../../../theme/useBrandLogo.js";
import { DeleteAccountDialog } from "../components/DeleteAccountDialog.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { displayInitial, displayName } from "../userDisplay.js";
import {
  deleteOwnAccount,
  resetPassword,
  updateProfile,
} from "../query/authApi.js";
import "../auth.css";
import "../settings.css";

function validateUsername(value) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (trimmed.length < 3 || trimmed.length > 24) {
    return "Username must be 3–24 characters.";
  }
  if (!/^[a-zA-Z0-9_]+$/.test(trimmed)) {
    return "Use only letters, numbers, and underscores.";
  }
  return "";
}

function PanelIcon({ children, danger = false }) {
  return (
    <span className={`set-panel-icon${danger ? " set-panel-icon-danger" : ""}`}>
      {children}
    </span>
  );
}

function Alert({ type, children }) {
  if (!children) return null;
  return (
    <p className={type === "ok" ? "set-alert set-alert-ok" : "auth-error set-alert"} role="alert">
      {children}
    </p>
  );
}

export function SettingsPage() {
  const { user, token, logout, updateUser } = useAuth();
  const navigate = useNavigate();
  const brandLogo = useBrandLogo();

  const [username, setUsername] = useState(user?.username || "");
  const [profileMsg, setProfileMsg] = useState(null);
  const [profileErr, setProfileErr] = useState(null);
  const [profileSaving, setProfileSaving] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwMsg, setPwMsg] = useState(null);
  const [pwErr, setPwErr] = useState(null);
  const [pwSaving, setPwSaving] = useState(false);

  const [deleteOpen, setDeleteOpen] = useState(false);

  const previewLabel = useMemo(() => {
    const trimmed = username.trim();
    if (trimmed) return `@${trimmed}`;
    return user?.email || "—";
  }, [username, user?.email]);

  const profileDirty =
    username.trim() !== (user?.username || "").trim();

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setProfileErr(null);
    setProfileMsg(null);
    const err = validateUsername(username);
    if (err) {
      setProfileErr(err);
      return;
    }
    setProfileSaving(true);
    try {
      const updated = await updateProfile(token, username.trim());
      updateUser(updated);
      setProfileMsg(username.trim() ? "Username updated." : "Username cleared.");
    } catch (ex) {
      setProfileErr(ex.message || String(ex));
    } finally {
      setProfileSaving(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setPwErr(null);
    setPwMsg(null);
    if (!user?.email) {
      setPwErr("Account email not found.");
      return;
    }
    if (!currentPassword) {
      setPwErr("Enter your current password.");
      return;
    }
    if (newPassword.length < 8) {
      setPwErr("New password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwErr("New passwords do not match.");
      return;
    }
    setPwSaving(true);
    try {
      await resetPassword(token, user.email, currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPwMsg("Password updated successfully.");
    } catch (ex) {
      setPwErr(ex.message || String(ex));
    } finally {
      setPwSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const handleDeleteAccount = async (password) => {
    await deleteOwnAccount(token, password);
    logout();
    navigate("/login", { replace: true });
  };

  const canDelete = !user?.is_admin;

  return (
    <div className="set-page prof-page">
      <div className="auth-bg" aria-hidden />
      <div className="set-wrap prof-container">
        <nav className="prof-nav">
          <Link to="/profile" className="auth-back">
            <span aria-hidden>←</span> Portfolios
          </Link>
          <div className="prof-nav-actions">
            <Link to="/" className="auth-btn auth-btn-ghost">
              Markets
            </Link>
          </div>
        </nav>

        <header className="set-hero prof-header">
          <div className="prof-header-main">
            <div className="prof-avatar-lg set-hero-avatar">{displayInitial(user)}</div>
            <div className="prof-header-copy">
              <div className="auth-brand-name">Account</div>
              <h1 className="prof-title">Settings</h1>
              <p className="set-hero-sub">
                Manage how you appear and sign in as{" "}
                <strong>{displayName(user)}</strong>
              </p>
              <div className="prof-chips">
                <span className={`prof-chip ${user?.is_admin ? "prof-chip-admin" : ""}`}>
                  {user?.is_admin ? "Admin" : "Member"}
                </span>
              </div>
            </div>
          </div>
          <div className="prof-brand">
            <img className="auth-brand-logo" src={brandLogo} alt="" />
          </div>
        </header>

        <div className="set-stack">
          <section className="set-panel" aria-labelledby="set-profile-title">
            <div className="set-panel-head">
              <PanelIcon>
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden>
                  <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.66-5.33-4-8-5Z" />
                </svg>
              </PanelIcon>
              <div className="set-panel-head-copy">
                <h2 id="set-profile-title" className="set-panel-title">
                  Public profile
                </h2>
                <p className="set-panel-desc">
                  Choose a username shown in the navbar and portfolio views instead of your email.
                </p>
              </div>
            </div>

            <div className="set-preview">
              <span className="set-preview-lbl">Displayed as</span>
              <span className="set-preview-val">{previewLabel}</span>
            </div>

            <form className="set-form" onSubmit={handleProfileSave}>
              <div className="auth-field">
                <label className="auth-label" htmlFor="set-username">
                  Username
                </label>
                <input
                  id="set-username"
                  className="auth-input"
                  type="text"
                  autoComplete="username"
                  placeholder="trader_k"
                  spellCheck={false}
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    setProfileMsg(null);
                    setProfileErr(null);
                  }}
                />
                <span className="auth-hint">3–24 characters · letters, numbers, underscore</span>
              </div>

              <div className="set-meta-row">
                <span className="set-meta-lbl">Email</span>
                <span className="set-meta-val">{user?.email || "—"}</span>
              </div>

              <Alert type="err">{profileErr}</Alert>
              <Alert type="ok">{profileMsg}</Alert>

              <button
                type="submit"
                className="auth-submit set-action"
                disabled={profileSaving || !profileDirty}
              >
                {profileSaving ? "Saving…" : "Save changes"}
              </button>
            </form>
          </section>

          <section className="set-panel" aria-labelledby="set-password-title">
            <div className="set-panel-head">
              <PanelIcon>
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden>
                  <path d="M18 8h-1V6a5 5 0 0 0-10 0v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2Zm-6 9a2 2 0 1 1 0-4 2 2 0 0 1 0 4Zm3.1-9H8.9V6a3.1 3.1 0 0 1 6.2 0v2Z" />
                </svg>
              </PanelIcon>
              <div className="set-panel-head-copy">
                <h2 id="set-password-title" className="set-panel-title">
                  Password
                </h2>
                <p className="set-panel-desc">
                  Confirm your current password, then choose a new one.
                </p>
              </div>
            </div>

            <form className="set-form" onSubmit={handleResetPassword}>
              <div className="set-meta-row">
                <span className="set-meta-lbl">Account</span>
                <span className="set-meta-val">{user?.email || "—"}</span>
              </div>

              <div className="auth-field">
                <label className="auth-label" htmlFor="set-pw-current">
                  Current password
                </label>
                <input
                  id="set-pw-current"
                  className="auth-input"
                  type="password"
                  autoComplete="current-password"
                  value={currentPassword}
                  onChange={(e) => {
                    setCurrentPassword(e.target.value);
                    setPwMsg(null);
                    setPwErr(null);
                  }}
                />
              </div>

              <div className="set-form-row">
                <div className="auth-field">
                  <label className="auth-label" htmlFor="set-pw-new">
                    New password
                  </label>
                  <input
                    id="set-pw-new"
                    className="auth-input"
                    type="password"
                    autoComplete="new-password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                  <span className="auth-hint">Minimum 8 characters</span>
                </div>
                <div className="auth-field">
                  <label className="auth-label" htmlFor="set-pw-confirm">
                    Confirm
                  </label>
                  <input
                    id="set-pw-confirm"
                    className="auth-input"
                    type="password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>
              </div>

              <Alert type="err">{pwErr}</Alert>
              <Alert type="ok">{pwMsg}</Alert>

              <button type="submit" className="auth-submit set-action" disabled={pwSaving}>
                {pwSaving ? "Updating…" : "Update password"}
              </button>
            </form>
          </section>

          <section className="set-panel set-panel-danger" aria-labelledby="set-session-title">
            <div className="set-panel-head">
              <PanelIcon danger>
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden>
                  <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5-5-5zM4 5h8V3H4a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" />
                </svg>
              </PanelIcon>
              <div className="set-panel-head-copy">
                <h2 id="set-session-title" className="set-panel-title">
                  Sign out
                </h2>
                <p className="set-panel-desc">
                  End your session on this device. You can sign back in anytime.
                </p>
              </div>
            </div>
            <button
              type="button"
              className="auth-btn auth-btn-danger set-logout"
              onClick={handleLogout}
            >
              Log out
            </button>
          </section>

          {canDelete ? (
            <section className="set-panel set-panel-danger" aria-labelledby="set-delete-title">
              <div className="set-panel-head">
                <PanelIcon danger>
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden>
                    <path d="M9 3v1H4v2h16V4h-5V3H9zm-3 5v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8H6zm3 2h2v9H9v-9zm4 0h2v9h-2v-9z" />
                  </svg>
                </PanelIcon>
                <div className="set-panel-head-copy">
                  <h2 id="set-delete-title" className="set-panel-title">
                    Delete account
                  </h2>
                  <p className="set-panel-desc">
                    Deactivate your account. You will no longer be able to log in. An
                    administrator can restore your account afterwards.
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="auth-btn auth-btn-danger set-logout"
                onClick={() => setDeleteOpen(true)}
              >
                Delete my account
              </button>
            </section>
          ) : null}
        </div>
      </div>

      <DeleteAccountDialog
        open={deleteOpen}
        email={user?.email}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDeleteAccount}
      />
    </div>
  );
}
