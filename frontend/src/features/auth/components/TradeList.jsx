import { TradeRow } from "./TradeRow.jsx";

export function TradeList({ trades }) {
  if (!trades || trades.length === 0) {
    return <div className="pd-empty">No trade history yet.</div>;
  }
  return (
    <div className="pd-trade-list">
      <div className="pd-trade-row pd-trade-head" aria-hidden>
        <div className="pd-trade-cell pd-trade-when">When</div>
        <div className="pd-trade-cell pd-trade-market">Market</div>
        <div className="pd-trade-cell pd-trade-num">Shares</div>
        <div className="pd-trade-cell pd-trade-num">Price</div>
        <div className="pd-trade-cell pd-trade-num">Total</div>
      </div>
      {trades.map((t) => (
        <TradeRow key={t.id} trade={t} />
      ))}
    </div>
  );
}
