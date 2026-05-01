import { useEffect, useMemo, useState } from "react";
import { formatNumber, formatPrice, formatUsd } from "../format.js";

function LivePriceTag({ status }) {
  if (status === "connected") {
    return (
      <span className="pd-live-pill pd-live-pill-on pd-live-pill-inline" title="Streaming live">
        <span className="pd-live-dot" aria-hidden />
        Live
      </span>
    );
  }
  if (status === "connecting") {
    return <span className="pd-live-pill pd-live-pill-inline">Connecting…</span>;
  }
  if (status === "error" || status === "closed") {
    return (
      <span
        className="pd-live-pill pd-live-pill-warn pd-live-pill-inline"
        title="Showing last known price"
      >
        Last known
      </span>
    );
  }
  return null;
}

function parseShares(raw) {
  const n = Number(String(raw ?? "").trim());
  if (!Number.isFinite(n) || n <= 0) return null;
  return n;
}

export function SellPositionDialog({ open, position, liveStatus, onClose, onSubmit }) {
  const [sharesInput, setSharesInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (open && position) {
      setSharesInput(String(position.shares ?? ""));
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

  const totalShares = position ? Number(position.shares) : 0;
  const sharesNum = parseShares(sharesInput);
  const sellAll =
    sharesNum !== null && Math.abs(sharesNum - totalShares) < 1e-9;
  const cur = position?.current_price;
  const proceeds = useMemo(() => {
    if (sharesNum === null || cur === null || cur === undefined) return null;
    const c = Number(cur);
    if (!Number.isFinite(c)) return null;
    return sharesNum * c;
  }, [sharesNum, cur]);

  if (!open || !position) return null;

  const overflow = sharesNum !== null && sharesNum > totalShares + 1e-9;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (busy) return;
    if (sharesNum === null) {
      setErr("Enter a positive number of shares.");
      return;
    }
    if (overflow) {
      setErr("You can't sell more shares than you hold.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await onSubmit({
        position_id: Number(position.id),
        shares: sellAll ? null : sharesNum,
      });
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
        aria-labelledby="sell-pos-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="sell-pos-title" className="prof-modal-title">
          Sell position
        </h2>
        <p className="prof-modal-sub">
          {position.market_question || position.market_id} ·{" "}
          <strong>{position.outcome}</strong>
        </p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <div className="bw-summary bw-summary-tight">
              <div className="bw-summary-row">
                <span className="bw-summary-lbl">Shares held</span>
                <span className="bw-summary-val">{formatNumber(totalShares, 4)}</span>
              </div>
              <div className="bw-summary-row">
                <span className="bw-summary-lbl">
                  Sell price (best bid)
                  <LivePriceTag status={liveStatus} />
                </span>
                <span className="bw-summary-val">{formatPrice(cur)}</span>
              </div>
            </div>
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="sell-shares">
              Shares to sell
            </label>
            <input
              id="sell-shares"
              className="auth-input"
              type="number"
              inputMode="decimal"
              min="0"
              step="any"
              value={sharesInput}
              onChange={(e) => setSharesInput(e.target.value)}
              autoFocus
            />
            <div className="pd-sell-quick">
              <button
                type="button"
                className="auth-btn auth-btn-ghost pd-sell-quick-btn"
                onClick={() => setSharesInput(String(totalShares / 2))}
                disabled={totalShares <= 0}
              >
                50%
              </button>
              <button
                type="button"
                className="auth-btn auth-btn-ghost pd-sell-quick-btn"
                onClick={() => setSharesInput(String(totalShares))}
                disabled={totalShares <= 0}
              >
                Max
              </button>
            </div>
          </div>

          <div className="bw-summary">
            <div className="bw-summary-row">
              <span className="bw-summary-lbl">Estimated proceeds</span>
              <span className="bw-summary-val bw-summary-good">
                {proceeds === null ? "—" : formatUsd(proceeds)}
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
              className="auth-btn auth-btn-primary"
              disabled={busy || sharesNum === null || overflow}
            >
              {busy ? "Selling…" : sellAll ? "Sell all" : "Sell shares"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
