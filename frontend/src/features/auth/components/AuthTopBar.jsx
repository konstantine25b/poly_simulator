import { Link } from "react-router-dom";
import { ThemeToggle } from "../../../theme/ThemeToggle.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { displayInitial, displayName } from "../userDisplay.js";
import "../auth.css";

export function AuthTopBar() {
  const { isAuthenticated, user, booting } = useAuth();

  if (booting) return <div className="auth-topbar" aria-hidden />;

  return (
    <div className="auth-topbar">
      <ThemeToggle className="auth-topbar-theme" />
      {isAuthenticated ? (
        <>
          <Link to="/profile" className="auth-topbar-user" title={user?.email || "View profile"}>
            <span className="auth-topbar-avatar">{displayInitial(user)}</span>
            <span className="auth-topbar-display">{displayName(user)}</span>
          </Link>
          <Link to="/settings" className="auth-btn auth-btn-ghost">
            Settings
          </Link>
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
