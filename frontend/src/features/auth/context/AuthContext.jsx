import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { fetchMe, loginUser, registerUser } from "../query/authApi.js";

const STORAGE_KEY = "poly.auth";

const AuthContext = createContext(null);

function readStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || !parsed.token) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeStored(value) {
  if (value) localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  else localStorage.removeItem(STORAGE_KEY);
}

export function AuthProvider({ children }) {
  const [state, setState] = useState(() => readStored());
  const [booting, setBooting] = useState(Boolean(readStored()));

  useEffect(() => {
    if (!state?.token) {
      setBooting(false);
      return;
    }
    let cancelled = false;
    fetchMe(state.token)
      .then((user) => {
        if (cancelled) return;
        const next = { token: state.token, user };
        setState(next);
        writeStored(next);
      })
      .catch(() => {
        if (cancelled) return;
        setState(null);
        writeStored(null);
      })
      .finally(() => {
        if (!cancelled) setBooting(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const applyAuthResponse = useCallback((resp) => {
    const next = { token: resp.access_token, user: resp.user };
    setState(next);
    writeStored(next);
    return next;
  }, []);

  const login = useCallback(
    async (email, password) => applyAuthResponse(await loginUser(email, password)),
    [applyAuthResponse],
  );

  const register = useCallback(
    async (email, password) => applyAuthResponse(await registerUser(email, password)),
    [applyAuthResponse],
  );

  const logout = useCallback(() => {
    setState(null);
    writeStored(null);
  }, []);

  const value = useMemo(
    () => ({
      user: state?.user || null,
      token: state?.token || null,
      isAuthenticated: Boolean(state?.token),
      booting,
      login,
      register,
      logout,
    }),
    [state, booting, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
