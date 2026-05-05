import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import polymarketMark from "../../assets/polymarket.jpg";
import { useAuth } from "../features/auth/context/AuthContext.jsx";
import { POLYPTRADE_X_URL } from "../social.js";
import "./navbar.css";

function initialFor(email) {
  if (!email) return "?";
  return email.trim().charAt(0).toUpperCase() || "?";
}

const MOBILE_NAV_MQ = "(max-width: 768px)";

export function Navbar() {
  const { isAuthenticated, user, logout, booting } = useAuth();
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

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
        <Link to="/" className="nav-brand">
          <img className="nav-brand-logo" src={polymarketMark} alt="" />
          <span className="nav-brand-text">
            <span className="nav-brand-name">Poly Simulator</span>
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
            {booting ? (
              <span className="nav-skel" aria-hidden />
            ) : isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="nav-user"
                  title="View profile"
                  onClick={() => setMenuOpen(false)}
                >
                  <span className="nav-avatar">{initialFor(user?.email)}</span>
                  <span className="nav-email">{user?.email}</span>
                </Link>
                <button
                  type="button"
                  className="nav-btn nav-btn-ghost"
                  onClick={() => {
                    setMenuOpen(false);
                    logout();
                  }}
                >
                  Log out
                </button>
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
