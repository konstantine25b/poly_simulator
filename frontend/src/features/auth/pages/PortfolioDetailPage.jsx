import { useCallback, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import polymarketMark from "../../../../assets/polymarket.jpg";
import { apiBase } from "../../../config.js";
import { LiveMarketQuoteSub } from "../../markets/query/LiveMarketQuoteSub.jsx";
import { PortfolioSummaryGrid } from "../components/PortfolioSummaryGrid.jsx";
import { PositionList } from "../components/PositionList.jsx";
import { SellPositionDialog } from "../components/SellPositionDialog.jsx";
import { SettlePositionDialog } from "../components/SettlePositionDialog.jsx";
import { TradeList } from "../components/TradeList.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { formatUsd, initialFor } from "../format.js";
import { usePortfolioDetail } from "../hooks/usePortfolioDetail.js";
import {
  computeStartingBalance,
  enrichPositionsWithLive,
  recomputeSummary,
  uniqueMarketRefs,
} from "../livePortfolio.js";
import { closePosition, settlePosition } from "../query/portfoliosApi.js";
import "../auth.css";
import "../portfolioDetail.css";

function liveAggregateStatus(liveByMarket, marketRefs) {
  if (marketRefs.length === 0) return "idle";
  let connected = 0;
  let connecting = 0;
  let errored = 0;
  for (const ref of marketRefs) {
    const s = liveByMarket[ref]?.connectionStatus;
    if (s === "connected") connected += 1;
    else if (s === "connecting" || !s) connecting += 1;
    else if (s === "error") errored += 1;
  }
  if (connected === marketRefs.length) return "connected";
  if (connected > 0) return "partial";
  if (errored > 0 && connecting === 0) return "error";
  return "connecting";
}

export function PortfolioDetailPage() {
  const { portfolioId } = useParams();
  const { user, token } = useAuth();
  const { data, loading, err, refresh } = usePortfolioDetail(token, portfolioId);

  const [sellTargetId, setSellTargetId] = useState(null);
  const [settleTargetId, setSettleTargetId] = useState(null);
  const [liveByMarket, setLiveByMarket] = useState({});

  const positions = data?.positions || [];
  const trades = data?.trades || [];
  const summaryBase = data?.summary;

  const marketRefs = useMemo(() => uniqueMarketRefs(positions), [positions]);
  const livePositions = useMemo(
    () => enrichPositionsWithLive(positions, liveByMarket),
    [positions, liveByMarket],
  );
  const liveSummary = useMemo(
    () => recomputeSummary(summaryBase, livePositions),
    [summaryBase, livePositions],
  );
  const startingBalance = useMemo(
    () => computeStartingBalance(summaryBase?.balance, trades),
    [summaryBase?.balance, trades],
  );
  const liveStatus = liveAggregateStatus(liveByMarket, marketRefs);

  const handleQuoteUpdate = useCallback((mref, entry) => {
    setLiveByMarket((prev) => {
      const old = prev[mref];
      if (
        old &&
        old.quotes === entry.quotes &&
        old.connectionStatus === entry.connectionStatus
      ) {
        return prev;
      }
      return { ...prev, [mref]: entry };
    });
  }, []);

  const findPosition = (id) =>
    livePositions.find((p) => Number(p.id) === Number(id)) || null;

  const sellTarget = sellTargetId !== null ? findPosition(sellTargetId) : null;
  const settleTarget =
    settleTargetId !== null ? findPosition(settleTargetId) : null;

  const handleSell = async (body) => {
    await closePosition(token, portfolioId, body);
    await refresh();
  };

  const handleSettle = async (body) => {
    await settlePosition(token, portfolioId, body);
    await refresh();
  };

  const summary = liveSummary || summaryBase;
  const name = summary?.name || (loading ? "Loading…" : `Portfolio #${portfolioId}`);

  return (
    <div className="prof-page pd-page">
      <div className="auth-bg" aria-hidden />

      {marketRefs.map((mref) => (
        <LiveMarketQuoteSub
          key={mref}
          apiBase={apiBase}
          marketRef={mref}
          onChange={handleQuoteUpdate}
        />
      ))}

      <div className="prof-container">
        <nav className="prof-nav">
          <Link to="/profile" className="auth-back">
            <span aria-hidden>←</span>
            All portfolios
          </Link>
          <div className="prof-nav-actions">
            <LiveStatusPill status={liveStatus} />
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
          <PortfolioSummaryGrid
            summary={summary}
            positionsCount={livePositions.length}
            startingBalance={startingBalance}
          />
        ) : null}

        <section className="prof-section">
          <div className="prof-section-head">
            <h2 className="prof-section-title">Open positions</h2>
            <span className="pd-section-count">{livePositions.length}</span>
          </div>
          <PositionList
            positions={livePositions}
            onSell={(p) => setSellTargetId(p.id)}
            onSettle={(p) => setSettleTargetId(p.id)}
          />
        </section>

        <section className="prof-section">
          <div className="prof-section-head">
            <h2 className="prof-section-title">Trade history</h2>
            <span className="pd-section-count">{trades.length}</span>
          </div>
          <TradeList trades={trades} />
        </section>
      </div>

      <SellPositionDialog
        open={Boolean(sellTarget)}
        position={sellTarget}
        liveStatus={sellTarget?.live_status}
        onClose={() => setSellTargetId(null)}
        onSubmit={handleSell}
      />
      <SettlePositionDialog
        open={Boolean(settleTarget)}
        position={settleTarget}
        onClose={() => setSettleTargetId(null)}
        onSubmit={handleSettle}
      />
    </div>
  );
}

function LiveStatusPill({ status }) {
  if (status === "idle") return null;
  let cls = "pd-live-pill";
  let label = "Live";
  let title = "Live prices streaming";
  if (status === "connected") {
    cls += " pd-live-pill-on";
  } else if (status === "partial") {
    cls += " pd-live-pill-on";
    label = "Live · partial";
    title = "Some markets streaming";
  } else if (status === "connecting") {
    label = "Connecting…";
    title = "Connecting to live feed";
  } else {
    cls += " pd-live-pill-warn";
    label = "Live unavailable";
    title = "Live feed unavailable";
  }
  const showDot = status === "connected" || status === "partial";
  return (
    <span className={cls} title={title}>
      {showDot ? <span className="pd-live-dot" aria-hidden /> : null}
      {label}
    </span>
  );
}
