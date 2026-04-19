import { field } from "./rowField.js";

export function parseMarketEndMs(market) {
  const ed = field(market, "endDate");
  if (ed) {
    const t = Date.parse(String(ed));
    if (!Number.isNaN(t)) return t;
  }
  const iso = field(market, "endDateIso");
  if (iso && typeof iso === "string") {
    const s = iso.trim();
    if (s.length === 10 && /^\d{4}-\d{2}-\d{2}$/.test(s)) {
      const t = Date.parse(`${s}T23:59:59.999Z`);
      if (!Number.isNaN(t)) return t;
    }
    const t2 = Date.parse(s);
    if (!Number.isNaN(t2)) return t2;
  }
  return null;
}

export function isMarketPastEnd(market, nowMs = Date.now()) {
  const endMs = parseMarketEndMs(market);
  if (endMs == null) return false;
  return nowMs > endMs;
}

export function shouldShowLiveBadge(market, nowMs = Date.now()) {
  const active = Number(field(market, "active")) === 1;
  const closed = Number(field(market, "closed")) === 1;
  if (!active || closed) return false;
  if (isMarketPastEnd(market, nowMs)) return false;
  return true;
}
