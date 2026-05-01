import { Link } from "react-router-dom";
import {
  formatDateTime,
  formatNumber,
  formatPrice,
  formatUsd,
  tradeSideMeta,
} from "../format.js";

export function TradeRow({ trade }) {
  const meta = tradeSideMeta(trade.side);
  const ref = trade.market_slug || trade.market_id;
  const href = ref ? `/m/${encodeURIComponent(ref)}` : null;
  const title = trade.market_question || trade.market_id;

  return (
    <div className="pd-trade-row">
      <div className="pd-trade-cell pd-trade-when">
        <span className="pd-trade-date">{formatDateTime(trade.traded_at)}</span>
        <span className={`pd-trade-side ${meta.className}`}>{meta.label}</span>
      </div>
      <div className="pd-trade-cell pd-trade-market">
        {href ? (
          <Link to={href} className="pd-trade-mkt pd-link">
            {title}
          </Link>
        ) : (
          <span className="pd-trade-mkt">{title}</span>
        )}
        <span className="pd-trade-outcome">{trade.outcome}</span>
      </div>
      <div className="pd-trade-cell pd-trade-num">
        <span className="pd-trade-lbl">Shares</span>
        <span className="pd-trade-val">{formatNumber(trade.shares, 4)}</span>
      </div>
      <div className="pd-trade-cell pd-trade-num">
        <span className="pd-trade-lbl">Price</span>
        <span className="pd-trade-val">{formatPrice(trade.price)}</span>
      </div>
      <div className="pd-trade-cell pd-trade-num">
        <span className="pd-trade-lbl">Total</span>
        <span className="pd-trade-val">{formatUsd(trade.total)}</span>
      </div>
    </div>
  );
}
