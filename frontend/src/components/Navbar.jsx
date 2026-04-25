import { Link, NavLink } from "react-router-dom";
import polymarketMark from "../../assets/polymarket.jpg";
import { useAuth } from "../features/auth/context/AuthContext.jsx";
import "./navbar.css";

function initialFor(email) {
  if (!email) return "?";
  return email.trim().charAt(0).toUpperCase() || "?";
}

export function Navbar() {
  const { isAuthenticated, user, logout, booting } = useAuth();

  return (
    <header className="nav-shell">
      <nav className="nav-bar" aria-label="Primary">
        <Link to="/" className="nav-brand">
          <img className="nav-brand-logo" src={polymarketMark} alt="" />
          <span className="nav-brand-text">
            <span className="nav-brand-name">Poly Simulator</span>
            <span className="nav-brand-tag">Paper trading</span>
          </span>
        </Link>

        <div className="nav-links">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `nav-link${isActive ? " nav-link-active" : ""}`
            }
          >
            Markets
          </NavLink>
          {isAuthenticated ? (
            <NavLink
              to="/profile"
              className={({ isActive }) =>
                `nav-link${isActive ? " nav-link-active" : ""}`
              }
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
              <Link to="/profile" className="nav-user" title="View profile">
                <span className="nav-avatar">{initialFor(user?.email)}</span>
                <span className="nav-email">{user?.email}</span>
              </Link>
              <button
                type="button"
                className="nav-btn nav-btn-ghost"
                onClick={logout}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-btn nav-btn-ghost">
                Log in
              </Link>
              <Link to="/register" className="nav-btn nav-btn-primary">
                Register
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
