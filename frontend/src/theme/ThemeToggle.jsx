import { useTheme } from "./ThemeContext.jsx";
import "./themeToggle.css";

export function ThemeToggle({ className = "" }) {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === "light";
  const label = isLight ? "Switch to dark mode" : "Switch to light mode";

  return (
    <button
      type="button"
      className={`theme-toggle${className ? ` ${className}` : ""}`}
      onClick={toggleTheme}
      aria-label={label}
      title={label}
    >
      {isLight ? (
        <svg className="theme-toggle-icon" viewBox="0 0 24 24" aria-hidden fill="currentColor">
          <path d="M21.64 13a1 1 0 0 0-1.05-.14 8.05 8.05 0 0 1-3.37.73 8.15 8.15 0 0 1-8.14-8.1 8.08 8.08 0 0 1 .86-3.66 1 1 0 0 0-1.26-1.28 10 10 0 1 0 13 13.05 1 1 0 0 0-.04-1.6z" />
        </svg>
      ) : (
        <svg className="theme-toggle-icon" viewBox="0 0 24 24" aria-hidden fill="currentColor">
          <path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.8 1.42-1.42zm10.48 0l1.79-1.79 1.41 1.41-1.79 1.8-1.41-1.42zM12 4V1h-1v3h1zm0 19v-3h-1v3h1zm8-9h3v-1h-3v1zM1 12h3v-1H1v1zm16.24 7.16l1.8 1.79 1.41-1.41-1.79-1.8-1.42 1.42zM6.76 19.16l-1.79 1.79-1.41-1.41 1.79-1.8 1.41 1.42zM12 18a6 6 0 1 1 0-12 6 6 0 0 1 0 12z" />
        </svg>
      )}
    </button>
  );
}
