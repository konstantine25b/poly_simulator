import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../features/auth/context/AuthContext.jsx";
import { displayInitial, displayName } from "../features/auth/userDisplay.js";
import { POLYPTRADE_X_URL } from "../social.js";
import { ThemeToggle } from "../theme/ThemeToggle.jsx";
import { useBrandLogo } from "../theme/useBrandLogo.js";
import "./navbar.css";

const MOBILE_NAV_MQ = "(max-width: 768px)";

export function Navbar() {
  const { isAuthenticated, user, booting } = useAuth();
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const brandLogo = useBrandLogo();

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const mq = window.matchMedia(MOBILE_NAV_MQ);
    const onKey = (e) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    const onResize = () => {
      if (!mq.matches) setMenuOpen(false);
    };
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    mq.addEventListener("change", onResize);
    window.addEventListener("resize", onResize);
    return () => {
      document.body.style.overflow = prevOverflow;
      document.removeEventListener("keydown", onKey);
      mq.removeEventListener("change", onResize);
      window.removeEventListener("resize", onResize);
    };
  }, [menuOpen]);

  return (
    <header className={`nav-shell${menuOpen ? " nav-menu-open" : ""}`}>
      <nav className="nav-bar" aria-label="Primary">
        <Link
          to="/"
          className="nav-brand"
          aria-label="PolyPTrade home"
          title="PolyPTrade — Paper trading"
        >
          <img className="nav-brand-logo" src={brandLogo} alt="PolyPTrade" />
          <span className="nav-brand-text">
            <span className="nav-brand-name">PolyPTrade</span>
            <span className="nav-brand-tag">Paper trading</span>
          </span>
        </Link>

        <div className="nav-panel" id="nav-primary-panel">
          <div className="nav-links">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `nav-link${isActive ? " nav-link-active" : ""}`
              }
              onClick={() => setMenuOpen(false)}
            >
              Markets
            </NavLink>
            {isAuthenticated ? (
              <NavLink
                to="/profile"
                className={({ isActive }) =>
                  `nav-link${isActive ? " nav-link-active" : ""}`
                }
                onClick={() => setMenuOpen(false)}
              >
                Portfolios
              </NavLink>
            ) : null}
          </div>

          <div className="nav-actions">
            <ThemeToggle />
            {booting ? (
              <span className="nav-skel" aria-hidden />
            ) : isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="nav-user"
                  title={user?.email || "View profile"}
                  onClick={() => setMenuOpen(false)}
                >
                  <span className="nav-avatar">{displayInitial(user)}</span>
                  <span className="nav-display">{displayName(user)}</span>
                </Link>
                <NavLink
                  to="/settings"
                  className={({ isActive }) =>
                    `nav-settings${isActive ? " nav-settings-active" : ""}`
                  }
                  aria-label="Settings"
                  title="Settings"
                  onClick={() => setMenuOpen(false)}
                >
                  <svg
                    className="nav-settings-icon"
                    viewBox="0 0 24 24"
                    width="20"
                    height="20"
                    fill="currentColor"
                    aria-hidden
                  >
                    <path d="M19.14 12.94c.04-.31.06-.63.06-.94s-.02-.63-.06-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58ZM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2Z" />
                  </svg>
                </NavLink>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="nav-btn nav-btn-ghost"
                  onClick={() => setMenuOpen(false)}
                >
                  Log in
                </Link>
                <Link
                  to="/register"
                  className="nav-btn nav-btn-primary"
                  onClick={() => setMenuOpen(false)}
                >
                  Register
                </Link>
              </>
            )}
            <a
              className="nav-x"
              href={POLYPTRADE_X_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="PolyPTrade on X"
            >
              <svg
                className="nav-x-icon"
                viewBox="0 0 24 24"
                aria-hidden
                fill="currentColor"
              >
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </a>
          </div>
        </div>

        <button
          type="button"
          className="nav-menu-toggle"
          aria-expanded={menuOpen}
          aria-controls="nav-primary-panel"
          onClick={() => setMenuOpen((o) => !o)}
        >
          <span className="nav-menu-toggle-box" aria-hidden>
            <span className="nav-menu-bar" />
            <span className="nav-menu-bar" />
            <span className="nav-menu-bar" />
          </span>
          <span className="nav-sr-only">
            {menuOpen ? "Close menu" : "Open menu"}
          </span>
        </button>
      </nav>
      <button
        type="button"
        className="nav-backdrop"
        aria-hidden
        tabIndex={-1}
        onClick={() => setMenuOpen(false)}
      />
    </header>
  );
}
