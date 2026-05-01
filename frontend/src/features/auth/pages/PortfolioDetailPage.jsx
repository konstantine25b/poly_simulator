import { Link, useParams } from "react-router-dom";
import polymarketMark from "../../../../assets/polymarket.jpg";
import { PortfolioSummaryGrid } from "../components/PortfolioSummaryGrid.jsx";
import { PositionList } from "../components/PositionList.jsx";
import { TradeList } from "../components/TradeList.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { formatUsd, initialFor } from "../format.js";
import { usePortfolioDetail } from "../hooks/usePortfolioDetail.js";
import "../auth.css";
import "../portfolioDetail.css";

export function PortfolioDetailPage() {
  const { portfolioId } = useParams();
  const { user, token } = useAuth();
  const { data, loading, err, refresh } = usePortfolioDetail(token, portfolioId);

  const summary = data?.summary;
  const positions = data?.positions || [];
  const trades = data?.trades || [];
  const name = summary?.name || (loading ? "Loading…" : `Portfolio #${portfolioId}`);

  return (
    <div className="prof-page pd-page">
      <div className="auth-bg" aria-hidden />
      <div className="prof-container">
        <nav className="prof-nav">
          <Link to="/profile" className="auth-back">
            <span aria-hidden>←</span>
            All portfolios
          </Link>
          <div className="prof-nav-actions">
            <button
              type="button"
              className="auth-btn auth-btn-ghost"
              onClick={refresh}
              disabled={loading}
            >
              Refresh
            </button>
          </div>
        </nav>

        <header className="prof-header pd-header">
          <div className="prof-header-main">
            <div className="prof-avatar-lg pd-avatar">{initialFor(name)}</div>
            <div className="prof-header-copy">
              <div className="auth-brand-name">Portfolio</div>
              <h1 className="prof-title">{name}</h1>
              <div className="pd-header-meta">
                {summary?.portfolio_id != null ? (
                  <span className="prof-chip">ID {summary.portfolio_id}</span>
                ) : null}
                {summary?.balance !== undefined ? (
                  <span className="prof-chip pd-chip-cash">
                    Cash {formatUsd(summary.balance)}
                  </span>
                ) : null}
                {user?.email ? (
                  <span className="prof-chip" title={user.email}>
                    {user.email}
                  </span>
                ) : null}
              </div>
            </div>
          </div>
          <div className="prof-brand">
            <img className="auth-brand-logo" src={polymarketMark} alt="" />
          </div>
        </header>

        {err ? <div className="prof-state prof-state-err">{err}</div> : null}
        {loading && !data ? (
          <div className="prof-state">Loading portfolio…</div>
        ) : null}

        {summary ? (
          <PortfolioSummaryGrid summary={summary} positionsCount={positions.length} />
        ) : null}

        <section className="prof-section">
          <div className="prof-section-head">
            <h2 className="prof-section-title">Open positions</h2>
            <span className="pd-section-count">{positions.length}</span>
          </div>
          <PositionList positions={positions} />
        </section>

        <section className="prof-section">
          <div className="prof-section-head">
            <h2 className="prof-section-title">Trade history</h2>
            <span className="pd-section-count">{trades.length}</span>
          </div>
          <TradeList trades={trades} />
        </section>
      </div>
    </div>
  );
}
