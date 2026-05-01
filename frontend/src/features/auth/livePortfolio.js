function asNumber(v) {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function computeSellPrice(quote) {
  if (!quote) return null;
  const bb = asNumber(quote.best_bid);
  if (bb !== null) return bb;
  const ba = asNumber(quote.best_ask);
  if (ba !== null) return ba;
  return null;
}

export function computeBuyPrice(quote) {
  if (!quote) return null;
  const ba = asNumber(quote.best_ask);
  if (ba !== null) return ba;
  const bb = asNumber(quote.best_bid);
  if (bb !== null) return bb;
  return null;
}

function findOutcomeQuote(quotes, outcome) {
  if (!quotes) return null;
  const lc = String(outcome || "").toLowerCase();
  return quotes.find((q) => String(q.outcome).toLowerCase() === lc) || null;
}

export function marketRefForPosition(position) {
  if (!position) return "";
  return String(position.market_slug || position.market_id || "");
}

export function enrichPositionWithLive(position, liveEntry) {
  if (!liveEntry) return position;
  const quote = findOutcomeQuote(liveEntry.quotes, position.outcome);
  const sell = computeSellPrice(quote);
  const status = liveEntry.connectionStatus;
  if (sell === null) {
    return { ...position, live_status: status };
  }
  const sh = asNumber(position.shares) ?? 0;
  const cost = asNumber(position.cost) ?? 0;
  const mv = sh * sell;
  return {
    ...position,
    current_price: sell,
    market_value: mv,
    unrealized_pnl: mv - cost,
    market_load_error: null,
    live_status: status,
  };
}

export function enrichPositionsWithLive(positions, liveByMarket) {
  if (!positions || positions.length === 0) return positions || [];
  return positions.map((p) => {
    const ref = marketRefForPosition(p);
    return enrichPositionWithLive(p, liveByMarket?.[ref]);
  });
}

export function recomputeSummary(baseSummary, livePositions) {
  if (!baseSummary) return baseSummary;
  if (!livePositions || livePositions.length === 0) return baseSummary;
  let invested = 0;
  let mv = 0;
  let pnl = 0;
  let any = false;
  for (const p of livePositions) {
    const cost = asNumber(p.cost);
    if (cost !== null) invested += cost;
    const v = asNumber(p.market_value);
    const u = asNumber(p.unrealized_pnl);
    if (v !== null) {
      mv += v;
      any = true;
    }
    if (u !== null) pnl += u;
  }
  if (!any) return baseSummary;
  const balance = asNumber(baseSummary.balance) ?? 0;
  return {
    ...baseSummary,
    total_invested: invested,
    positions_market_value: mv,
    unrealized_pnl: pnl,
    equity: balance + mv,
  };
}

export function uniqueMarketRefs(positions) {
  const set = new Set();
  for (const p of positions || []) {
    const ref = marketRefForPosition(p);
    if (ref) set.add(ref);
  }
  return Array.from(set);
}

export function computeStartingBalance(currentBalance, trades) {
  const cash = asNumber(currentBalance);
  if (cash === null) return null;
  let cashOut = 0;
  let cashIn = 0;
  for (const t of trades || []) {
    const total = asNumber(t.total);
    if (total === null) continue;
    if (t.side === "buy") {
      cashOut += total;
    } else if (t.side === "sell" || t.side === "settle_win") {
      cashIn += total;
    }
  }
  return cash + cashOut - cashIn;
}
