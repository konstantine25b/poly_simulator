import { computeStartingBalance } from "../livePortfolio.js";

const EPS = 1e-8;

const TRADE_HEADERS = [
  "id",
  "portfolio_id",
  "traded_at",
  "side",
  "market_id",
  "market_slug",
  "market_question",
  "outcome",
  "shares",
  "price",
  "total",
  "cost_basis",
  "realized_pnl",
  "pnl_result",
];

function csvCell(value) {
  if (value === null || value === undefined) return "";
  const s = String(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function csvRow(values) {
  return values.map(csvCell).join(",");
}

function posKey(marketId, outcome) {
  return `${String(marketId)}|${String(outcome || "").toLowerCase()}`;
}

function asNum(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function pnlResultFromRealized(r) {
  if (!Number.isFinite(r)) return "";
  if (r > EPS) return "win";
  if (r < -EPS) return "loss";
  return "breakeven";
}

function sortTradesAsc(trades) {
  return [...(trades || [])].sort((a, b) => {
    const ta = String(a.traded_at || "");
    const tb = String(b.traded_at || "");
    if (ta !== tb) return ta.localeCompare(tb);
    return Number(a.id) - Number(b.id);
  });
}

function replayTradesForPnl(sortedAsc) {
  const book = new Map();
  const getPos = (key) => {
    if (!book.has(key)) book.set(key, { shares: 0, cost: 0 });
    return book.get(key);
  };

  let sumRealized = 0;
  let closedWin = 0;
  let closedLoss = 0;
  let closedBreakeven = 0;
  let buyNotional = 0;
  let sellProceeds = 0;
  let settleWinProceeds = 0;
  let buyLegs = 0;
  let sellLegs = 0;
  let settleWinLegs = 0;
  let settleLossLegs = 0;

  const rows = [];

  for (const t of sortedAsc) {
    const key = posKey(t.market_id, t.outcome);
    const pos = getPos(key);
    const shares = asNum(t.shares);
    const total = asNum(t.total);
    const side = String(t.side || "");

    let costBasis = "";
    let realizedPnl = "";
    let pnlResult = "";

    if (side === "buy") {
      buyLegs += 1;
      pos.shares += shares;
      pos.cost += total;
      buyNotional += total;
      costBasis = total;
      realizedPnl = "";
      pnlResult = "open";
    } else if (side === "sell") {
      sellLegs += 1;
      const basis =
        pos.shares > EPS ? (pos.cost / pos.shares) * shares : 0;
      const r = total - basis;
      sellProceeds += total;
      sumRealized += r;
      if (r > EPS) closedWin += 1;
      else if (r < -EPS) closedLoss += 1;
      else closedBreakeven += 1;
      costBasis = basis;
      realizedPnl = r;
      pnlResult = pnlResultFromRealized(r);
      pos.shares -= shares;
      pos.cost -= basis;
      if (pos.shares < EPS) {
        pos.shares = 0;
        pos.cost = 0;
      }
    } else if (side === "settle_win") {
      settleWinLegs += 1;
      const basis = pos.cost;
      const r = total - basis;
      settleWinProceeds += total;
      sumRealized += r;
      if (r > EPS) closedWin += 1;
      else if (r < -EPS) closedLoss += 1;
      else closedBreakeven += 1;
      costBasis = basis;
      realizedPnl = r;
      pnlResult = pnlResultFromRealized(r);
      pos.shares = 0;
      pos.cost = 0;
    } else if (side === "settle_loss") {
      settleLossLegs += 1;
      const basis = pos.cost;
      const r = -basis;
      sumRealized += r;
      closedLoss += 1;
      costBasis = basis;
      realizedPnl = r;
      pnlResult = "loss";
      pos.shares = 0;
      pos.cost = 0;
    }

    rows.push({
      trade: t,
      costBasis,
      realizedPnl,
      pnlResult,
    });
  }

  return {
    rows,
    agg: {
      sum_realized_pnl: sumRealized,
      closed_trades_win: closedWin,
      closed_trades_loss: closedLoss,
      closed_trades_breakeven: closedBreakeven,
      total_buy_notional: buyNotional,
      total_sell_proceeds: sellProceeds,
      total_settle_win_proceeds: settleWinProceeds,
      buy_leg_count: buyLegs,
      sell_leg_count: sellLegs,
      settle_win_leg_count: settleWinLegs,
      settle_loss_leg_count: settleLossLegs,
    },
  };
}

function pushMetric(lines, metric, value) {
  lines.push(csvRow([metric, value === null || value === undefined ? "" : value]));
}

function buildStatsSection(summary, trades, agg) {
  const lines = [];
  lines.push(csvRow(["metric", "value"]));
  const iso = new Date().toISOString();
  pushMetric(lines, "generated_at", iso);
  if (summary) {
    pushMetric(lines, "portfolio_id", summary.portfolio_id);
    pushMetric(lines, "portfolio_name", summary.name);
    pushMetric(lines, "cash_balance", summary.balance);
    pushMetric(lines, "equity", summary.equity);
    pushMetric(lines, "open_invested", summary.total_invested);
    pushMetric(lines, "positions_market_value", summary.positions_market_value);
    pushMetric(lines, "unrealized_pnl_open_book", summary.unrealized_pnl);
  }
  const start = summary ? computeStartingBalance(summary.balance, trades) : null;
  if (start !== null && start !== undefined) {
    pushMetric(lines, "starting_balance", start);
  }
  const eq = summary != null ? Number(summary.equity) : NaN;
  if (Number.isFinite(eq) && start !== null && start !== undefined && Number.isFinite(Number(start))) {
    const st = Number(start);
    const totalPnl = eq - st;
    pushMetric(lines, "total_pnl_vs_start", totalPnl);
    if (st > EPS) {
      pushMetric(lines, "total_return_pct_vs_start", ((totalPnl / st) * 100).toFixed(6));
    }
  }
  pushMetric(lines, "trade_row_count", trades.length);
  pushMetric(lines, "sum_realized_pnl_historical", agg.sum_realized_pnl);
  pushMetric(lines, "closed_legs_win_count", agg.closed_trades_win);
  pushMetric(lines, "closed_legs_loss_count", agg.closed_trades_loss);
  pushMetric(lines, "closed_legs_breakeven_count", agg.closed_trades_breakeven);
  pushMetric(lines, "total_buy_notional", agg.total_buy_notional);
  pushMetric(lines, "total_sell_proceeds", agg.total_sell_proceeds);
  pushMetric(lines, "total_settle_win_proceeds", agg.total_settle_win_proceeds);
  pushMetric(lines, "buy_leg_count", agg.buy_leg_count);
  pushMetric(lines, "sell_leg_count", agg.sell_leg_count);
  pushMetric(lines, "settle_win_leg_count", agg.settle_win_leg_count);
  pushMetric(lines, "settle_loss_leg_count", agg.settle_loss_leg_count);
  return lines;
}

export function buildPortfolioTradesCsv(trades, summary) {
  const sorted = sortTradesAsc(trades);
  const { rows: enriched, agg } = replayTradesForPnl(sorted);
  const lines = [];
  lines.push(...buildStatsSection(summary || null, sorted, agg));
  lines.push("");
  lines.push(csvRow(TRADE_HEADERS));
  for (const row of enriched) {
    const t = row.trade;
    lines.push(
      csvRow([
        t.id,
        t.portfolio_id,
        t.traded_at,
        t.side,
        t.market_id,
        t.market_slug,
        t.market_question,
        t.outcome,
        t.shares,
        t.price,
        t.total,
        row.costBasis,
        row.realizedPnl,
        row.pnlResult,
      ]),
    );
  }
  return lines.join("\r\n");
}

export function downloadTextFile(filename, text, mimeType) {
  const blob = new Blob([text], { type: mimeType || "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function safeFilenamePart(s) {
  return String(s || "portfolio")
    .replace(/[^\w\-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80) || "portfolio";
}
