import { useState } from "react";
import { Link } from "react-router-dom";
import polymarketMark from "../../../../assets/polymarket.jpg";
import { NewPortfolioDialog } from "../components/NewPortfolioDialog.jsx";
import { PortfolioCard } from "../components/PortfolioCard.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useProfileData } from "../hooks/useProfileData.js";
import "../auth.css";

function formatUsd(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

function initialFor(email) {
  if (!email) return "?";
  return email.trim().charAt(0).toUpperCase() || "?";
}

function sum(values) {
  return values.reduce((acc, v) => acc + (Number.isFinite(Number(v)) ? Number(v) : 0), 0);
}

export function ProfilePage() {
  const { user, token, logout } = useAuth();
  const isAdmin = Boolean(user?.is_admin);
  const { items, loading, err, creating, create, refresh } = useProfileData(
    token,
    user?.id,
    isAdmin,
  );
  const [dialogOpen, setDialogOpen] = useState(false);

  const totalCash = sum(items.map((p) => p.balance));
  const totalEquity = sum(items.map((p) => p.summary?.equity ?? p.balance));
  const totalInvested = sum(items.map((p) => p.summary?.total_invested));
  const totalPnl = sum(items.map((p) => p.summary?.unrealized_pnl));
  const scopeLabel = isAdmin ? "all users" : "you";

  return (
    <div className="prof-page">
      <div className="auth-bg" aria-hidden />
      <div className="prof-container">
        <nav className="prof-nav">
          <Link to="/" className="auth-back">
            <span aria-hidden>←</span> Back to markets
          </Link>
          <div className="prof-nav-actions">
            <button type="button" className="auth-btn auth-btn-ghost" onClick={refresh}>
              Refresh
            </button>
            <button type="button" className="auth-btn auth-btn-ghost" onClick={logout}>
              Log out
            </button>
          </div>
        </nav>

        <header className="prof-header">
          <div className="prof-header-main">
            <div className="prof-avatar-lg">{initialFor(user?.email)}</div>
            <div className="prof-header-copy">
              <div className="auth-brand-name">Your profile</div>
              <h1 className="prof-title">{user?.email || "—"}</h1>
              <div className="prof-chips">
                <span className={`prof-chip ${user?.is_admin ? "prof-chip-admin" : ""}`}>
                  {user?.is_admin ? "Admin" : "Member"}
                </span>
              </div>
            </div>
          </div>
          <div className="prof-brand">
            <img className="auth-brand-logo" src={polymarketMark} alt="" />
          </div>
        </header>

        <section className="prof-summary">
          <div className="prof-summary-card prof-summary-card-hero">
            <span className="prof-summary-lbl">Total equity</span>
            <span className="prof-summary-val">{formatUsd(totalEquity)}</span>
            <span className="prof-summary-hint">
              Across {items.length} portfolio{items.length === 1 ? "" : "s"} ({scopeLabel})
            </span>
          </div>
          <div className="prof-summary-card">
            <span className="prof-summary-lbl">Cash balance</span>
            <span className="prof-summary-val">{formatUsd(totalCash)}</span>
          </div>
          <div className="prof-summary-card">
            <span className="prof-summary-lbl">Invested</span>
            <span className="prof-summary-val">{formatUsd(totalInvested)}</span>
          </div>
          <div className="prof-summary-card">
            <span className="prof-summary-lbl">Total profit / loss</span>
            <span
              className={`prof-summary-val ${
                totalPnl > 0 ? "prof-pnl-pos" : totalPnl < 0 ? "prof-pnl-neg" : ""
              }`}
            >
              {formatUsd(totalPnl)}
            </span>
          </div>
        </section>

        <section className="prof-section">
          <div className="prof-section-head">
            <h2 className="prof-section-title">
              {isAdmin ? "All portfolios" : "Portfolios"}
            </h2>
            <button
              type="button"
              className="auth-btn auth-btn-primary"
              onClick={() => setDialogOpen(true)}
              disabled={creating}
            >
              New portfolio
            </button>
          </div>

          {loading ? <div className="prof-state">Loading portfolios…</div> : null}
          {err ? <div className="prof-state prof-state-err">{err}</div> : null}
          {!loading && !err && items.length === 0 ? (
            <div className="prof-empty">
              <p>You don&apos;t have any portfolios yet.</p>
              <button
                type="button"
                className="auth-btn auth-btn-primary"
                onClick={() => setDialogOpen(true)}
                disabled={creating}
              >
                Create my first portfolio
              </button>
            </div>
          ) : null}

          <div className="prof-port-list">
            {items.map((p) => (
              <PortfolioCard key={p.id} portfolio={p} />
            ))}
          </div>
        </section>
      </div>

      <NewPortfolioDialog
        open={dialogOpen}
        busy={creating}
        onClose={() => setDialogOpen(false)}
        onSubmit={create}
      />
    </div>
  );
}
