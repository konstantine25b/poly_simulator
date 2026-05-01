import { formatUsd, pnlClass } from "../format.js";

function pctLabel(pct) {
  if (pct === null) return null;
  return `${pct > 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

export function PortfolioSummaryGrid({ summary, positionsCount, startingBalance }) {
  const equity = summary?.equity;
  const balance = summary?.balance;
  const invested = summary?.total_invested;
  const marketValue = summary?.positions_market_value;
  const pnl = summary?.unrealized_pnl;

  const investedNum = Number(invested);
  const pnlNum = Number(pnl);
  const investedPct =
    Number.isFinite(investedNum) && investedNum > 0 && Number.isFinite(pnlNum)
      ? (pnlNum / investedNum) * 100
      : null;

  const equityNum = Number(equity);
  const startNum = Number(startingBalance);
  const totalReturn =
    Number.isFinite(equityNum) && Number.isFinite(startNum)
      ? equityNum - startNum
      : null;
  const totalReturnPct =
    totalReturn !== null && startNum > 0 ? (totalReturn / startNum) * 100 : null;

  return (
    <section className="prof-summary pd-summary">
      <div className="prof-summary-card prof-summary-card-hero">
        <span className="prof-summary-lbl">Total equity</span>
        <span className="prof-summary-val">{formatUsd(equity)}</span>
        <span className="prof-summary-hint">
          {positionsCount} open position{positionsCount === 1 ? "" : "s"}
        </span>
      </div>
      <div className="prof-summary-card">
        <span className="prof-summary-lbl">Cash</span>
        <span className="prof-summary-val">{formatUsd(balance)}</span>
      </div>
      <div className="prof-summary-card">
        <span className="prof-summary-lbl">Invested</span>
        <span className="prof-summary-val">{formatUsd(invested)}</span>
      </div>
      <div className="prof-summary-card">
        <span className="prof-summary-lbl">Market value</span>
        <span className="prof-summary-val">{formatUsd(marketValue)}</span>
      </div>
      <div className="prof-summary-card">
        <span className="prof-summary-lbl">Profit / loss</span>
        <span className={`prof-summary-val ${pnlClass(pnl)}`}>
          {formatUsd(pnl, { signed: true })}
        </span>
        {investedPct !== null ? (
          <span className={`pd-summary-pct ${pnlClass(pnl)}`}>
            {pctLabel(investedPct)}
          </span>
        ) : null}
      </div>
      <div className="prof-summary-card">
        <span className="prof-summary-lbl">Return vs start</span>
        <span className={`prof-summary-val ${pnlClass(totalReturn)}`}>
          {totalReturn === null ? "—" : formatUsd(totalReturn, { signed: true })}
        </span>
        {totalReturnPct !== null ? (
          <span className={`pd-summary-pct ${pnlClass(totalReturn)}`}>
            {pctLabel(totalReturnPct)}
          </span>
        ) : null}
        {startNum > 0 ? (
          <span className="prof-summary-hint">
            Started with {formatUsd(startNum)}
          </span>
        ) : null}
      </div>
    </section>
  );
}
