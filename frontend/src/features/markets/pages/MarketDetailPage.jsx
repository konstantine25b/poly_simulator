import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiBase } from "../../../config.js";
import { DETAIL_SECTIONS, formatDetailValue, pickField } from "../detailSections.js";
import { fetchMarketDetail } from "../query/fetchMarketDetail.js";
import "../marketDetail.css";

function formatQuote(n) {
  if (n === null || n === undefined) return "-";
  const x = Number(n);
  if (Number.isNaN(x)) return String(n);
  return x.toFixed(4);
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

  return (
    <div className="md-page">
      <nav className="md-nav">
        <Link to="/" className="md-back">
          ← Markets
        </Link>
      </nav>
      {loading ? <p className="md-state">Loading…</p> : null}
      {err ? <p className="md-state md-err">{err}</p> : null}
      {market ? (
        <>
          <header className="md-head">
            <h1 className="md-title">{pickField(market, "question") || pickField(market, "id")}</h1>
            <div className="md-badges">
              {data.closed ? <span className="md-badge md-badge-closed">Closed</span> : null}
              {!data.closed ? <span className="md-badge md-badge-open">Open</span> : null}
              <span className="md-badge md-badge-src">
                Data: {data.source === "database" ? "database" : "live (Polymarket)"}
              </span>
              {data.stale ? <span className="md-badge md-badge-stale">Stale snapshot (live unavailable)</span> : null}
            </div>
            {pickField(market, "slug") ? (
              <p className="md-slug">
                <span className="md-slug-lbl">Slug</span> {pickField(market, "slug")}
              </p>
            ) : null}
          </header>

          {!data.closed && data.best_quotes && data.best_quotes.length > 0 ? (
            <section className="md-section">
              <h2 className="md-h2">Best bid / best ask (CLOB)</h2>
              <table className="md-table">
                <thead>
                  <tr>
                    <th>Outcome</th>
                    <th>Best bid</th>
                    <th>Best ask</th>
                  </tr>
                </thead>
                <tbody>
                  {data.best_quotes.map((row) => (
                    <tr key={row.token_id}>
                      <td>{row.outcome}</td>
                      <td>{formatQuote(row.best_bid)}</td>
                      <td>{formatQuote(row.best_ask)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ) : null}

          {DETAIL_SECTIONS.map(([title, keys]) => {
            const rows = keys
              .map((k) => {
                const raw = pickField(market, k);
                const text = formatDetailValue(raw);
                if (text === null) return null;
                return (
                  <div key={k} className="md-row">
                    <dt className="md-dt">{k}</dt>
                    <dd className="md-dd">{text.includes("\n") ? <pre className="md-pre">{text}</pre> : text}</dd>
                  </div>
                );
              })
              .filter(Boolean);
            if (rows.length === 0) return null;
            return (
              <section key={title} className="md-section">
                <h2 className="md-h2">{title}</h2>
                <dl className="md-dl">{rows}</dl>
              </section>
            );
          })}
        </>
      ) : null}
    </div>
  );
}
