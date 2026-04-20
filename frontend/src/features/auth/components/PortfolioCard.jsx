function formatUsd(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

function formatDate(s) {
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return String(s);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function pnlClass(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "";
  const v = Number(n);
  if (v > 0) return "prof-pnl-pos";
  if (v < 0) return "prof-pnl-neg";
  return "";
}

export function PortfolioCard({ portfolio, onDelete }) {
  const s = portfolio.summary;
  return (
    <div className="prof-port-card">
      <div className="prof-port-head">
        <div className="prof-port-head-text">
          <div className="prof-port-name">{portfolio.name}</div>
          <div className="prof-port-meta">
            Created {formatDate(portfolio.created_at)} · ID {portfolio.id}
          </div>
          {portfolio.owner_email || portfolio.user_id != null ? (
            <div className="prof-port-owner" title={portfolio.owner_email || ""}>
              <span className="prof-port-owner-lbl">Owner</span>
              <span className="prof-port-owner-val">
                {portfolio.owner_email || `user #${portfolio.user_id}`}
              </span>
            </div>
          ) : null}
        </div>
        <div className="prof-port-right">
          <div className="prof-port-balance">
            <span className="prof-port-balance-lbl">Cash</span>
            <span className="prof-port-balance-val">{formatUsd(portfolio.balance)}</span>
          </div>
          {onDelete ? (
            <button
              type="button"
              className="prof-port-delete"
              onClick={() => onDelete(portfolio)}
              title="Delete portfolio"
              aria-label={`Delete portfolio ${portfolio.name}`}
            >
              Delete
            </button>
          ) : null}
        </div>
      </div>
      {s ? (
        <div className="prof-port-stats">
          <div className="prof-stat">
            <span className="prof-stat-lbl">Equity</span>
            <span className="prof-stat-val">{formatUsd(s.equity)}</span>
          </div>
          <div className="prof-stat">
            <span className="prof-stat-lbl">Invested</span>
            <span className="prof-stat-val">{formatUsd(s.total_invested)}</span>
          </div>
          <div className="prof-stat">
            <span className="prof-stat-lbl">Market value</span>
            <span className="prof-stat-val">{formatUsd(s.positions_market_value)}</span>
          </div>
          <div className="prof-stat">
            <span className="prof-stat-lbl">Profit / loss</span>
            <span className={`prof-stat-val ${pnlClass(s.unrealized_pnl)}`}>
              {formatUsd(s.unrealized_pnl)}
            </span>
          </div>
        </div>
      ) : (
        <div className="prof-port-stats-empty">Summary unavailable.</div>
      )}
    </div>
  );
}
