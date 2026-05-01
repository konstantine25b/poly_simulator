import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { formatPrice, formatUsd } from "../format.js";
import { useUserPortfolios } from "../hooks/useUserPortfolios.js";
import { placeBet } from "../query/portfoliosApi.js";
import "../portfolioDetail.css";

function findQuote(quotes, outcome) {
  if (!quotes) return null;
  const lc = String(outcome || "").toLowerCase();
  return quotes.find((q) => String(q.outcome).toLowerCase() === lc) || null;
}

function parseShares(raw) {
  const n = Number(String(raw ?? "").trim());
  if (!Number.isFinite(n) || n <= 0) return null;
  return n;
}

export function BetWidget({ marketId, quotes, disabled }) {
  const outcomes = useMemo(
    () => (quotes || []).map((q) => String(q.outcome)),
    [quotes],
  );
  const { token, user, isAuthenticated } = useAuth();
  const isAdmin = Boolean(user?.is_admin);
  const { items, loading, err: portErr, refresh } = useUserPortfolios(
    token,
    user?.id,
    isAdmin,
  );

  const [portfolioId, setPortfolioId] = useState("");
  const [outcome, setOutcome] = useState("");
  const [shares, setShares] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (!portfolioId && items.length > 0) setPortfolioId(String(items[0].id));
  }, [items, portfolioId]);

  useEffect(() => {
    if (!outcome && outcomes && outcomes.length > 0) setOutcome(String(outcomes[0]));
  }, [outcomes, outcome]);

  const selectedPortfolio = useMemo(
    () => items.find((p) => String(p.id) === String(portfolioId)) || null,
    [items, portfolioId],
  );

  const sharesNum = parseShares(shares);
  const quote = findQuote(quotes, outcome);
  const buyPrice = quote?.best_ask;
  const estCost =
    sharesNum !== null && Number.isFinite(Number(buyPrice))
      ? sharesNum * Number(buyPrice)
      : null;

  const cash = selectedPortfolio ? Number(selectedPortfolio.balance) : null;
  const insufficient =
    estCost !== null && cash !== null && estCost > cash + 1e-9;
  const canSubmit =
    !disabled &&
    !busy &&
    Boolean(token) &&
    Boolean(marketId) &&
    Boolean(outcome) &&
    sharesNum !== null &&
    Boolean(portfolioId) &&
    !insufficient;

  if (!isAuthenticated) {
    return (
      <section className="md-panel bw-panel">
        <h2 className="md-panel-title md-panel-title-inline">Place a bet</h2>
        <p className="bw-locked">
          <Link to="/login" className="bw-link">
            Log in
          </Link>{" "}
          or{" "}
          <Link to="/register" className="bw-link">
            create an account
          </Link>{" "}
          to start paper trading on this market.
        </p>
      </section>
    );
  }

  if (disabled) {
    return (
      <section className="md-panel bw-panel">
        <h2 className="md-panel-title md-panel-title-inline">Place a bet</h2>
        <p className="bw-locked">This market is closed — new bets are disabled.</p>
      </section>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setErr(null);
    setSuccess(null);
    try {
      const result = await placeBet(token, portfolioId, {
        market_id: String(marketId),
        outcome,
        shares: sharesNum,
      });
      setSuccess({
        shares: result.shares,
        price: result.price,
        cost: result.cost,
        outcome: result.outcome,
        portfolioId: result.portfolio_id,
      });
      setShares("");
      refresh();
    } catch (ex) {
      setErr(ex.message || String(ex));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="md-panel bw-panel">
      <div className="bw-head">
        <h2 className="md-panel-title md-panel-title-inline">Place a bet</h2>
        {selectedPortfolio ? (
          <span className="bw-cash" title="Available cash">
            Cash {formatUsd(selectedPortfolio.balance)}
          </span>
        ) : null}
      </div>

      <form className="bw-form" onSubmit={handleSubmit} noValidate>
        <div className="bw-field">
          <label className="bw-label" htmlFor="bw-portfolio">
            Portfolio
          </label>
          <select
            id="bw-portfolio"
            className="bw-input"
            value={portfolioId}
            onChange={(e) => setPortfolioId(e.target.value)}
            disabled={loading || items.length === 0 || busy}
          >
            {items.length === 0 ? (
              <option value="">{loading ? "Loading…" : "No portfolios"}</option>
            ) : null}
            {items.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} · {formatUsd(p.balance)}
              </option>
            ))}
          </select>
          {portErr ? <span className="bw-hint bw-hint-warn">{portErr}</span> : null}
          {items.length === 0 && !loading ? (
            <span className="bw-hint">
              <Link to="/profile" className="bw-link">
                Create a portfolio
              </Link>{" "}
              first to start trading.
            </span>
          ) : null}
        </div>

        {outcomes && outcomes.length > 0 ? (
          <div className="bw-field">
            <span className="bw-label">Outcome</span>
            <div className="bw-outcomes" role="radiogroup" aria-label="Outcome">
              {outcomes.map((o) => {
                const q = findQuote(quotes, o);
                const ask = q?.best_ask;
                const active = String(o) === String(outcome);
                return (
                  <button
                    key={String(o)}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    className={`bw-outcome${active ? " bw-outcome-active" : ""}`}
                    onClick={() => setOutcome(String(o))}
                    disabled={busy}
                  >
                    <span className="bw-outcome-name">{String(o)}</span>
                    <span className="bw-outcome-price">
                      {ask !== null && ask !== undefined ? formatPrice(ask) : "—"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}

        <div className="bw-field">
          <label className="bw-label" htmlFor="bw-shares">
            Shares
          </label>
          <input
            id="bw-shares"
            className="bw-input"
            type="number"
            inputMode="decimal"
            min="0"
            step="any"
            placeholder="e.g. 10"
            value={shares}
            onChange={(e) => setShares(e.target.value)}
            disabled={busy}
          />
          <span className="bw-hint">
            Each share pays $1.00 if your outcome wins.
          </span>
        </div>

        <div className="bw-summary">
          <div className="bw-summary-row">
            <span className="bw-summary-lbl">Buy price</span>
            <span className="bw-summary-val">
              {buyPrice !== null && buyPrice !== undefined
                ? formatPrice(buyPrice)
                : "—"}
            </span>
          </div>
          <div className="bw-summary-row">
            <span className="bw-summary-lbl">Estimated cost</span>
            <span
              className={`bw-summary-val${insufficient ? " bw-summary-bad" : ""}`}
            >
              {estCost !== null ? formatUsd(estCost) : "—"}
            </span>
          </div>
          <div className="bw-summary-row">
            <span className="bw-summary-lbl">Max payout if wins</span>
            <span className="bw-summary-val bw-summary-good">
              {sharesNum !== null ? formatUsd(sharesNum) : "—"}
            </span>
          </div>
        </div>

        {insufficient ? (
          <p className="auth-error">
            Insufficient cash in this portfolio. Pick another or reduce shares.
          </p>
        ) : null}
        {err ? <p className="auth-error">{err}</p> : null}
        {success ? (
          <p className="bw-success">
            Bought {Number(success.shares).toLocaleString()} share
            {Number(success.shares) === 1 ? "" : "s"} of {success.outcome} at{" "}
            {formatPrice(success.price)} for {formatUsd(success.cost)}.{" "}
            <Link to={`/portfolios/${success.portfolioId}`} className="bw-link">
              View portfolio
            </Link>
          </p>
        ) : null}

        <button
          type="submit"
          className="auth-btn auth-btn-primary bw-submit"
          disabled={!canSubmit}
        >
          {busy
            ? "Placing bet…"
            : estCost !== null
              ? `Buy ${outcome} for ${formatUsd(estCost)}`
              : "Buy"}
        </button>
      </form>
    </section>
  );
}
