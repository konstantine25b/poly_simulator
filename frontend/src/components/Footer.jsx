import { POLYPTRADE_X_URL } from "../social.js";
import "./footer.css";

export function Footer() {
  return (
    <footer className="footer-shell">
      <div className="footer-bar">
        <p className="footer-copy">© 2026 PolyPTrade. All rights reserved.</p>
        <a
          className="footer-x"
          href={POLYPTRADE_X_URL}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="PolyPTrade on X"
        >
          <svg
            className="footer-x-icon"
            viewBox="0 0 24 24"
            aria-hidden
            fill="currentColor"
          >
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
          </svg>
          X
        </a>
      </div>
    </footer>
  );
}
