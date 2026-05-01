import { Link } from "react-router-dom";
import {
  formatDateShort,
  formatNumber,
  formatPrice,
  formatUsd,
  pnlClass,
} from "../format.js";

function pnlPct(cost, pnl) {
  const c = Number(cost);
  const p = Number(pnl);
  if (!Number.isFinite(c) || c <= 0 || !Number.isFinite(p)) return null;
  return (p / c) * 100;
}

export function PositionRow({ position, onSell, onSettle }) {
  const shares = Number(position.shares);
  const avg = Number(position.avg_price);
  const cost = Number(position.cost);
  const cur = position.current_price;
  const mv = position.market_value;
  const pnl = position.unrealized_pnl;
  const pnlPctVal = cur === null || cur === undefined ? null : pnlPct(cost, pnl);
  const errorMsg = position.market_load_error;
  const ref = position.market_slug || position.market_id;
  const detailHref = ref ? `/m/${encodeURIComponent(ref)}` : null;
  const title = position.market_question || position.market_id;

  return (
    <div className="pd-pos-card">
      <div className="pd-pos-head">
        <div className="pd-pos-titles">
          {detailHref ? (
            <Link to={detailHref} className="pd-pos-title pd-link">
              {title}
            </Link>
          ) : (
            <span className="pd-pos-title">{title}</span>
          )}
          <div className="pd-pos-sub">
            <span className="pd-pos-outcome">{position.outcome}</span>
            <span className="pd-pos-meta">
              Opened {formatDateShort(position.opened_at)}
            </span>
          </div>
        </div>
        <div className="pd-pos-pnl-wrap">
          <span className="pd-pos-pnl-lbl">Profit / loss</span>
          <span className={`pd-pos-pnl-val ${pnlClass(pnl)}`}>
            {pnl === null || pnl === undefined ? "—" : formatUsd(pnl, { signed: true })}
          </span>
          {pnlPctVal !== null ? (
            <span className={`pd-pos-pnl-pct ${pnlClass(pnl)}`}>
              {`${pnlPctVal > 0 ? "+" : ""}${pnlPctVal.toFixed(2)}%`}
            </span>
          ) : null}
        </div>
      </div>

      <div className="pd-pos-stats">
        <div className="pd-stat">
          <span className="pd-stat-lbl">Shares</span>
          <span className="pd-stat-val">{formatNumber(shares, 4)}</span>
        </div>
        <div className="pd-stat">
          <span className="pd-stat-lbl">Avg price</span>
          <span className="pd-stat-val">{formatPrice(avg)}</span>
        </div>
        <div className="pd-stat">
          <span className="pd-stat-lbl">Current (bid)</span>
          <span className="pd-stat-val">{formatPrice(cur)}</span>
        </div>
        <div className="pd-stat">
          <span className="pd-stat-lbl">Cost</span>
          <span className="pd-stat-val">{formatUsd(cost)}</span>
        </div>
        <div className="pd-stat">
          <span className="pd-stat-lbl">Market value</span>
          <span className="pd-stat-val">
            {mv === null || mv === undefined ? "—" : formatUsd(mv)}
          </span>
        </div>
      </div>

      {errorMsg ? <div className="pd-pos-warn">{errorMsg}</div> : null}

      {onSell || onSettle ? (
        <div className="pd-pos-actions">
          {onSell && !errorMsg ? (
            <button
              type="button"
              className="auth-btn auth-btn-primary pd-pos-action"
              onClick={() => onSell(position)}
            >
              Sell
            </button>
          ) : null}
          {onSettle ? (
            <button
              type="button"
              className="auth-btn auth-btn-ghost pd-pos-action"
              onClick={() => onSettle(position)}
            >
              Settle
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
