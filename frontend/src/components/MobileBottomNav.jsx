import { NavLink } from "react-router-dom";
import { useAuth } from "../features/auth/context/AuthContext.jsx";
import "./mobileBottomNav.css";

export function MobileBottomNav() {
  const { isAuthenticated, booting } = useAuth();

  return (
    <nav className="mob-nav" aria-label="Mobile primary">
      <NavLink
        to="/"
        end
        className={({ isActive }) => `mob-nav-item${isActive ? " mob-nav-item-active" : ""}`}
      >
        <span className="mob-nav-icon" aria-hidden>
          <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
            <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5Z" />
          </svg>
        </span>
        <span className="mob-nav-label">Markets</span>
      </NavLink>
      {booting ? (
        <span className="mob-nav-item mob-nav-item-disabled" aria-hidden>
          <span className="mob-nav-icon mob-nav-skel" />
          <span className="mob-nav-label mob-nav-skel mob-nav-skel-text" />
        </span>
      ) : isAuthenticated ? (
        <NavLink
          to="/profile"
          className={({ isActive }) => `mob-nav-item${isActive ? " mob-nav-item-active" : ""}`}
        >
          <span className="mob-nav-icon" aria-hidden>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5Z" />
            </svg>
          </span>
          <span className="mob-nav-label">Portfolios</span>
        </NavLink>
      ) : (
        <NavLink
          to="/login"
          className={({ isActive }) => `mob-nav-item${isActive ? " mob-nav-item-active" : ""}`}
        >
          <span className="mob-nav-icon" aria-hidden>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M11 7 9.6 8.4l2.15 2.15H3v2h8.75L9.6 14.6 11 16l5-5-5-5Zm8 9h-6v2h6a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-6v2h6v10Z" />
            </svg>
          </span>
          <span className="mob-nav-label">Log in</span>
        </NavLink>
      )}
      {booting ? (
        <span className="mob-nav-item mob-nav-item-disabled" aria-hidden>
          <span className="mob-nav-icon mob-nav-skel" />
          <span className="mob-nav-label mob-nav-skel mob-nav-skel-text" />
        </span>
      ) : isAuthenticated ? (
        <NavLink
          to="/settings"
          className={({ isActive }) => `mob-nav-item${isActive ? " mob-nav-item-active" : ""}`}
        >
          <span className="mob-nav-icon" aria-hidden>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M19.14 12.94c.04-.31.06-.63.06-.94s-.02-.63-.06-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z" />
            </svg>
          </span>
          <span className="mob-nav-label">Settings</span>
        </NavLink>
      ) : (
        <NavLink
          to="/register"
          className={({ isActive }) => `mob-nav-item${isActive ? " mob-nav-item-active" : ""}`}
        >
          <span className="mob-nav-icon" aria-hidden>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4Zm-9 2v-2H4v2H2v2h2v2h2v-2h2v-2H6Zm9 4c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4Z" />
            </svg>
          </span>
          <span className="mob-nav-label">Register</span>
        </NavLink>
      )}
    </nav>
  );
}
