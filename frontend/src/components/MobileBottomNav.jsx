import { NavLink } from "react-router-dom";
import { useAuth } from "../features/auth/context/AuthContext.jsx";
import { POLYPTRADE_X_URL } from "../social.js";
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
        <a
          className="mob-nav-item"
          href={POLYPTRADE_X_URL}
          target="_blank"
          rel="noopener noreferrer"
        >
          <span className="mob-nav-icon" aria-hidden>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
          </span>
          <span className="mob-nav-label">Community</span>
        </a>
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
