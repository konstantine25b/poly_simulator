import { createContext, useContext, useLayoutEffect, useMemo, useState } from "react";

const STORAGE_KEY = "poly-ptrade-theme";

const ThemeContext = createContext(null);

function readStoredTheme() {
  try {
    let v = localStorage.getItem(STORAGE_KEY);
    if (v == null) {
      v = localStorage.getItem("poly-sim-theme");
      if (v != null) localStorage.setItem(STORAGE_KEY, v);
    }
    return v === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => readStoredTheme());

  useLayoutEffect(() => {
    applyTheme(theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {}
  }, [theme]);

  const setTheme = (next) => {
    setThemeState(next === "light" ? "light" : "dark");
  };

  const toggleTheme = () => {
    setThemeState((t) => (t === "light" ? "dark" : "light"));
  };

  const value = useMemo(() => ({ theme, setTheme, toggleTheme }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return ctx;
}
