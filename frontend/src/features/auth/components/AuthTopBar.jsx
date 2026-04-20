import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import "../auth.css";

function initialFor(email) {
  if (!email) return "?";
  const trimmed = email.trim();
  return trimmed.charAt(0).toUpperCase() || "?";
}

export function AuthTopBar() {
  const { isAuthenticated, user, logout, booting } = useAuth();

  if (booting) return <div className="auth-topbar" aria-hidden />;

  return (
    <div className="auth-topbar">
      {isAuthenticated ? (
        <>
          <Link to="/profile" className="auth-topbar-user" title="View profile">
            <span className="auth-topbar-avatar">{initialFor(user?.email)}</span>
            <span className="auth-topbar-email">{user?.email}</span>
          </Link>
          <button type="button" className="auth-btn auth-btn-ghost" onClick={logout}>
            Log out
          </button>
        </>
      ) : (
        <>
          <Link to="/login" className="auth-btn auth-btn-ghost">
            Log in
          </Link>
          <Link to="/register" className="auth-btn auth-btn-primary">
            Register
          </Link>
        </>
      )}
    </div>
  );
}
