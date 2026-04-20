import { useEffect, useState } from "react";

function parseBalance(raw) {
  const trimmed = String(raw ?? "").trim();
  if (!trimmed) return { value: null };
  const n = Number(trimmed);
  if (!Number.isFinite(n)) return { error: "Balance must be a number." };
  if (n < 0) return { error: "Balance must be zero or positive." };
  return { value: n };
}

export function NewPortfolioDialog({ open, busy, onClose, onSubmit }) {
  const [name, setName] = useState("");
  const [balance, setBalance] = useState("");
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (open) {
      setName("");
      setBalance("");
      setErr(null);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (busy) return;
    const parsed = parseBalance(balance);
    if (parsed.error) {
      setErr(parsed.error);
      return;
    }
    const body = {};
    const trimmedName = name.trim();
    if (trimmedName) body.name = trimmedName;
    if (parsed.value !== null) body.balance = parsed.value;

    setErr(null);
    try {
      await onSubmit(body);
      onClose();
    } catch (ex) {
      setErr(ex.message || String(ex));
    }
  };

  return (
    <div className="prof-modal-backdrop" onClick={busy ? undefined : onClose}>
      <div
        className="prof-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-port-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="new-port-title" className="prof-modal-title">
          New portfolio
        </h2>
        <p className="prof-modal-sub">Give it a name and a starting cash balance. Both are optional.</p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label className="auth-label" htmlFor="np-name">
              Name
            </label>
            <input
              id="np-name"
              className="auth-input"
              type="text"
              placeholder="e.g. Main account"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={64}
              autoFocus
            />
            <span className="auth-hint">Leave blank to auto-name (portfolio1, portfolio2, …).</span>
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="np-balance">
              Starting balance (USD)
            </label>
            <input
              id="np-balance"
              className="auth-input"
              type="number"
              inputMode="decimal"
              min="0"
              step="0.01"
              placeholder="e.g. 1000"
              value={balance}
              onChange={(e) => setBalance(e.target.value)}
            />
            <span className="auth-hint">Leave blank to use the default paper balance.</span>
          </div>

          {err ? <p className="auth-error">{err}</p> : null}

          <div className="prof-modal-actions">
            <button
              type="button"
              className="auth-btn auth-btn-ghost"
              onClick={onClose}
              disabled={busy}
            >
              Cancel
            </button>
            <button type="submit" className="auth-btn auth-btn-primary" disabled={busy}>
              {busy ? "Creating…" : "Create portfolio"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
