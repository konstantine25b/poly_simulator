import { Link } from "react-router-dom";
import { formatDateShort, formatUsd, pnlClass } from "../format.js";
import "../portfolioDetail.css";

function handleDeleteClick(e, onDelete, portfolio) {
  e.preventDefault();
  e.stopPropagation();
  if (onDelete) onDelete(portfolio);
}

function handleRestoreClick(e, onRestore, portfolio) {
  e.preventDefault();
  e.stopPropagation();
  if (onRestore) onRestore(portfolio);
}

export function PortfolioCard({ portfolio, onDelete, onRestore }) {
  const s = portfolio.summary;
  const detailHref = `/portfolios/${encodeURIComponent(portfolio.id)}`;
  const ownerDeleted = Boolean(portfolio.owner_deleted);

  return (
    <Link to={detailHref} className="pd-port-card-link">
      <div className={`prof-port-card${ownerDeleted ? " prof-port-card-deleted" : ""}`}>
        <div className="prof-port-head">
          <div className="prof-port-head-text">
            <div className="prof-port-name">{portfolio.name}</div>
            <div className="prof-port-meta">
              Created {formatDateShort(portfolio.created_at)} · ID{" "}
              {portfolio.id}
            </div>
            {portfolio.owner_label || portfolio.user_id != null ? (
              <div
                className="prof-port-owner"
                title={portfolio.owner_email || ""}
              >
                <span className="prof-port-owner-lbl">Owner</span>
                <span className="prof-port-owner-val">
                  {portfolio.owner_label || `user #${portfolio.user_id}`}
                </span>
                {ownerDeleted ? (
                  <span className="prof-port-deleted-badge">Deleted account</span>
                ) : null}
              </div>
            ) : null}
          </div>
          <div className="prof-port-right">
            <div className="prof-port-balance">
              <span className="prof-port-balance-lbl">Cash</span>
              <span className="prof-port-balance-val">
                {formatUsd(portfolio.balance)}
              </span>
            </div>
            {ownerDeleted && onRestore ? (
              <button
                type="button"
                className="prof-port-restore"
                onClick={(e) => handleRestoreClick(e, onRestore, portfolio)}
                title="Restore account"
                aria-label={`Restore account for ${portfolio.owner_label || portfolio.user_id}`}
              >
                Restore account
              </button>
            ) : null}
            {onDelete ? (
              <button
                type="button"
                className="prof-port-delete"
                onClick={(e) => handleDeleteClick(e, onDelete, portfolio)}
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
              <span className="prof-stat-val">
                {formatUsd(s.total_invested)}
              </span>
            </div>
            <div className="prof-stat">
              <span className="prof-stat-lbl">Market value</span>
              <span className="prof-stat-val">
                {formatUsd(s.positions_market_value)}
              </span>
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
    </Link>
  );
}
