import { field, parseJsonArray } from "./rowField.js";

export function outcomeCount(market) {
  return parseJsonArray(field(market, "outcomes")).length;
}

export function outcomePairs(market) {
  const labels = parseJsonArray(field(market, "outcomes"));
  const prices = parseJsonArray(field(market, "outcomePrices"));
  const n = Math.max(labels.length, prices.length);
  const out = [];
  for (let i = 0; i < n; i += 1) {
    const lbl = labels[i];
    const prc = prices[i];
    const hasLabel = lbl != null && String(lbl).trim() !== "";
    const hasPrice = prc != null && String(prc).trim() !== "";
    if (!hasLabel || !hasPrice) continue;
    const num = Number(prc);
    if (Number.isNaN(num)) continue;
    out.push({ label: String(lbl).trim(), price: prc });
  }
  return out;
}
