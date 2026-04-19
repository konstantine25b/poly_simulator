import { useCallback, useEffect, useState } from "react";

const apiBase = import.meta.env.DEV ? "/api" : import.meta.env.VITE_API_URL || "";

async function apiGet(path) {
  const res = await fetch(`${apiBase}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

async function apiPost(path, body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      if (j.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [healthErr, setHealthErr] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState(() => localStorage.getItem("access_token") || "");
  const [authErr, setAuthErr] = useState(null);
  const [markets, setMarkets] = useState(null);
  const [marketsErr, setMarketsErr] = useState(null);
  const [marketsLoading, setMarketsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiGet("/health")
      .then((data) => {
        if (!cancelled) {
          setHealth(data);
          setHealthErr(null);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setHealth(null);
          setHealthErr(e.message || String(e));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const persistToken = useCallback((t) => {
    setToken(t);
    if (t) localStorage.setItem("access_token", t);
    else localStorage.removeItem("access_token");
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthErr(null);
    try {
      const data = await apiPost("/auth/login", { email, password });
      persistToken(data.access_token);
    } catch (err) {
      setAuthErr(err.message || String(err));
    }
  };

  const handleLogout = () => {
    persistToken("");
    setMarkets(null);
    setMarketsErr(null);
  };

  const loadMarkets = async () => {
    setMarketsLoading(true);
    setMarketsErr(null);
    try {
      const data = await apiGet("/db/markets?limit=10&offset=0&active=true&closed=false");
      setMarkets(data);
    } catch (err) {
      setMarkets(null);
      setMarketsErr(err.message || String(err));
    } finally {
      setMarketsLoading(false);
    }
  };

  return (
    <div style={{ padding: "1.5rem", maxWidth: 720 }}>
      <h1 style={{ marginTop: 0 }}>Poly Simulator</h1>
      <p className="muted">
        Paper trading UI. Start the API on port 8000, then run <code>npm run dev</code> here.
        Requests use the Vite proxy <code>/api</code> → <code>http://127.0.0.1:8000</code>.
      </p>

      <section className="card" style={{ marginTop: "1.5rem" }}>
        <h2 style={{ marginTop: 0 }}>API health</h2>
        {health && <pre style={{ margin: 0 }}>{JSON.stringify(health, null, 2)}</pre>}
        {healthErr && <p className="err">{healthErr}</p>}
      </section>

      <section className="card" style={{ marginTop: "1.25rem" }}>
        <h2 style={{ marginTop: 0 }}>Login</h2>
        {token ? (
          <div>
            <p className="muted">You have a saved access token.</p>
            <button type="button" onClick={handleLogout}>
              Log out
            </button>
          </div>
        ) : (
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: "0.75rem" }}>
              <input
                type="email"
                autoComplete="username"
                placeholder="Email"
                value={email}
                onChange={(ev) => setEmail(ev.target.value)}
              />
            </div>
            <div style={{ marginBottom: "0.75rem" }}>
              <input
                type="password"
                autoComplete="current-password"
                placeholder="Password"
                value={password}
                onChange={(ev) => setPassword(ev.target.value)}
              />
            </div>
            <button type="submit">Log in</button>
            {authErr && <p className="err">{authErr}</p>}
          </form>
        )}
      </section>

      <section className="card" style={{ marginTop: "1.25rem" }}>
        <h2 style={{ marginTop: 0 }}>Markets (sample)</h2>
        <p className="muted">Public: first 10 active markets from your local DB.</p>
        <button type="button" onClick={loadMarkets} disabled={marketsLoading}>
          {marketsLoading ? "Loading…" : "Load markets"}
        </button>
        {marketsErr && <p className="err">{marketsErr}</p>}
        {markets && markets.items && (
          <ul style={{ paddingLeft: "1.25rem" }}>
            {markets.items.map((m) => (
              <li key={m.id} style={{ marginBottom: "0.5rem" }}>
                <strong>{m.question || m.slug || m.id}</strong>
                {m.slug && (
                  <div className="muted" style={{ fontSize: "0.8rem" }}>
                    {m.slug}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
