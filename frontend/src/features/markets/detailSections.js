export const DETAIL_SECTIONS = [
  ["Identity", ["id", "question", "slug", "conditionId", "questionID", "marketType"]],
  ["Dates", ["startDate", "endDate", "startDateIso", "endDateIso", "createdAt", "updatedAt", "closedTime", "acceptingOrdersTimestamp"]],
  ["Status", ["active", "closed", "acceptingOrders", "enableOrderBook", "restricted", "archived", "featured", "negRisk", "resolvedBy"]],
  ["Prices", ["lastTradePrice", "bestBid", "bestAsk", "spread", "oneDayPriceChange", "oneWeekPriceChange", "oneMonthPriceChange"]],
  ["Volume & liquidity", ["volumeNum", "liquidityNum", "volume24hr", "volume1wk", "volume1mo", "volume1yr", "volumeClob", "liquidityClob"]],
  ["Outcomes", ["outcomes", "outcomePrices", "clobTokenIds"]],
  ["Event", ["event_title", "event_slug"]],
  ["Description", ["description"]],
  ["Resolution", ["resolutionSource", "umaBond", "umaReward"]],
  ["Rewards & orders", ["rewardsMinSize", "rewardsMaxSpread", "orderPriceMinTickSize", "orderMinSize"]],
  ["Other", ["image", "icon", "category", "tags"]],
];

export function formatDetailValue(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "object") {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

export function pickField(market, key) {
  if (market == null) return undefined;
  const v = market[key];
  if (v !== undefined && v !== null && v !== "") return v;
  const low = key.toLowerCase();
  if (market[low] !== undefined && market[low] !== null && market[low] !== "") return market[low];
  return undefined;
}
