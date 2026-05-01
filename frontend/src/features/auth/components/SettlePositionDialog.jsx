import { useEffect, useState } from "react";
import { formatNumber, formatUsd } from "../format.js";

export function SettlePositionDialog({ open, position, onClose, onSubmit }) {
  const [won, setWon] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (open) {
      setWon(true);
      setBusy(false);
      setErr(null);
    }
  }, [open, position?.id]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  if (!open || !position) return null;

  const totalShares = Number(position.shares);
  const payout = won ? totalShares : 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setErr(null);
    try {
      await onSubmit({ position_id: Number(position.id), won });
      onClose();
    } catch (ex) {
      setErr(ex.message || String(ex));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="prof-modal-backdrop" onClick={busy ? undefined : onClose}>
      <div
        className="prof-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settle-pos-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="settle-pos-title" className="prof-modal-title">
          Settle position
        </h2>
        <p className="prof-modal-sub">
          {position.market_question || position.market_id} ·{" "}
          <strong>{position.outcome}</strong>
        </p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <span className="auth-label">Outcome of this side</span>
            <div className="pd-settle-toggle" role="radiogroup">
              <button
                type="button"
                role="radio"
                aria-checked={won}
                className={`pd-settle-opt pd-settle-opt-win${won ? " pd-settle-opt-active" : ""}`}
                onClick={() => setWon(true)}
                disabled={busy}
              >
                Won · pays $1.00 / share
              </button>
              <button
                type="button"
                role="radio"
                aria-checked={!won}
                className={`pd-settle-opt pd-settle-opt-loss${!won ? " pd-settle-opt-active" : ""}`}
                onClick={() => setWon(false)}
                disabled={busy}
              >
                Lost · pays $0.00
              </button>
            </div>
          </div>

          <div className="bw-summary">
            <div className="bw-summary-row">
              <span className="bw-summary-lbl">Shares</span>
              <span className="bw-summary-val">{formatNumber(totalShares, 4)}</span>
            </div>
            <div className="bw-summary-row">
              <span className="bw-summary-lbl">Payout</span>
              <span className={`bw-summary-val ${won ? "bw-summary-good" : "bw-summary-bad"}`}>
                {formatUsd(payout)}
              </span>
            </div>
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
            <button
              type="submit"
              className={`auth-btn ${won ? "auth-btn-primary" : "auth-btn-danger"}`}
              disabled={busy}
            >
              {busy ? "Settling…" : won ? "Settle as won" : "Settle as lost"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
