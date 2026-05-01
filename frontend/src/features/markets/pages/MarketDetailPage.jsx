import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import polymarketMark from "../../../../assets/polymarket.jpg";
import { BetWidget } from "../../auth/components/BetWidget.jsx";
import { apiBase } from "../../../config.js";
import { DETAIL_SECTIONS, formatDetailValue, pickField } from "../detailSections.js";
import { fetchMarketDetail } from "../query/fetchMarketDetail.js";
import { useLiveBestQuotes } from "../query/useLiveBestQuotes.js";
import "../marketDetail.css";

function formatQuote(n) {
  if (n === null || n === undefined) return "-";
  const x = Number(n);
  if (Number.isNaN(x)) return String(n);
  return x.toFixed(4);
}

function humanKey(key) {
  return key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase()).trim();
}

export function MarketDetailPage() {
  const { marketRef } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!marketRef) return;
    let cancelled = false;
    setLoading(true);
    setErr(null);
    setData(null);
    fetchMarketDetail(apiBase, marketRef)
      .then((json) => {
        if (!cancelled) setData(json);
      })
      .catch((e) => {
        if (!cancelled) setErr(e.message || String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [marketRef]);

  const market = data?.market;
  const wsEnabled = Boolean(data && !data.closed && data.best_quotes?.length);
  const { quotes: liveQuotes, connectionStatus } = useLiveBestQuotes(
    apiBase,
    marketRef,
    wsEnabled,
    data?.best_quotes,
  );
  const img = market ? pickField(market, "image") || pickField(market, "icon") : null;
  const title = market ? pickField(market, "question") || pickField(market, "id") : "";
  const slug = market ? pickField(market, "slug") : null;
  const mid = market ? pickField(market, "id") : null;

  return (
    <div className="md-page">
      <div className="md-bg" aria-hidden />
      <nav className="md-nav">
        <Link to="/" className="md-back">
          <span className="md-back-icon" aria-hidden>
            ←
          </span>
          Markets
        </Link>
      </nav>

      {loading ? (
        <div className="md-skeleton" aria-busy="true">
          <div className="md-skel-hero" />
          <div className="md-skel-line" />
          <div className="md-skel-line md-skel-short" />
        </div>
      ) : null}

      {err ? (
        <div className="md-error-card">
          <p className="md-error-title">Could not load market</p>
          <p className="md-error-msg">{err}</p>
          <Link to="/" className="md-error-link">
            Back to browse
          </Link>
        </div>
      ) : null}

      {market ? (
        <>
          <header className="md-hero">
            <div className="md-hero-glow" aria-hidden />
            <div className="md-hero-inner">
              <div className="md-hero-visual">
                <img
                  className="md-hero-img"
                  src={img || polymarketMark}
                  alt=""
                  onError={(ev) => {
                    ev.currentTarget.onerror = null;
                    ev.currentTarget.src = polymarketMark;
                  }}
                />
              </div>
              <div className="md-hero-copy">
                <h1 className="md-title">{title}</h1>
                <div className="md-meta">
                  {mid ? (
                    <span className="md-chip md-chip-id">
                      ID <code>{mid}</code>
                    </span>
                  ) : null}
                  {slug ? (
                    <span className="md-chip md-chip-slug" title={slug}>
                      {slug}
                    </span>
                  ) : null}
                </div>
                <div className="md-badges">
                  {data.closed ? (
                    <span className="md-badge md-badge-closed">
                      <span className="md-badge-dot" />
                      Closed
                    </span>
                  ) : (
                    <span className="md-badge md-badge-open">
                      <span className="md-badge-dot" />
                      Open
                    </span>
                  )}
                  <span className="md-badge md-badge-src">
                    {data.source === "database" ? "From your database" : "Live from Polymarket"}
                  </span>
                  {data.stale ? (
                    <span className="md-badge md-badge-stale">Stale snapshot — live feed unavailable</span>
                  ) : null}
                </div>
              </div>
            </div>
          </header>

          {data && mid ? (
            <BetWidget
              marketId={mid}
              quotes={liveQuotes}
              disabled={Boolean(data.closed)}
            />
          ) : null}

          {!data.closed && liveQuotes && liveQuotes.length > 0 ? (
            <section className="md-panel md-quotes-section">
              <div className="md-panel-head">
                <div className="md-panel-head-row">
                  <h2 className="md-panel-title">Order book top</h2>
                  {connectionStatus === "connected" ? (
                    <span className="md-live-pill" title="Streaming best bid / ask from the order book">
                      <span className="md-live-dot" aria-hidden />
                      Live
                    </span>
                  ) : connectionStatus === "connecting" ? (
                    <span className="md-live-pill md-live-pill-muted">Connecting…</span>
                  ) : connectionStatus === "error" || connectionStatus === "closed" ? (
                    <span className="md-live-pill md-live-pill-warn" title="Live stream stopped; showing last known quotes">
                      {connectionStatus === "closed" ? "Live ended" : "Live unavailable"}
                    </span>
                  ) : null}
                </div>
                <p className="md-panel-sub">Best bid and best ask per outcome (CLOB)</p>
              </div>
              <div className="md-quotes-grid">
                {liveQuotes.map((row) => (
                  <div key={row.token_id} className="md-quote-card">
                    <div className="md-quote-outcome">{row.outcome}</div>
                    <div className="md-quote-pair">
                      <div className="md-quote-metric">
                        <span className="md-quote-lbl">Best bid</span>
                        <span className="md-quote-val md-quote-bid">{formatQuote(row.best_bid)}</span>
                      </div>
                      <div className="md-quote-div" aria-hidden />
                      <div className="md-quote-metric">
                        <span className="md-quote-lbl">Best ask</span>
                        <span className="md-quote-val md-quote-ask">{formatQuote(row.best_ask)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          <div className="md-panels">
            {DETAIL_SECTIONS.map(([title, keys]) => {
              const rows = keys
                .map((k) => {
                  const raw = pickField(market, k);
                  const text = formatDetailValue(raw);
                  if (text === null) return null;
                  return (
                    <div key={k} className="md-row">
                      <dt className="md-dt">{humanKey(k)}</dt>
                      <dd className="md-dd">
                        {text.includes("\n") ? <pre className="md-pre">{text}</pre> : text}
                      </dd>
                    </div>
                  );
                })
                .filter(Boolean);
              if (rows.length === 0) return null;
              const full = title === "Description";
              return (
                <section key={title} className={`md-panel${full ? " md-panel-full" : ""}`}>
                  <h2 className="md-panel-title md-panel-title-inline">{title}</h2>
                  <dl className="md-dl">{rows}</dl>
                </section>
              );
            })}
          </div>
        </>
      ) : null}
    </div>
  );
}
