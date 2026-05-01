export function formatUsd(n, opts) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  const sign = opts && opts.signed && Number(n) > 0 ? "+" : "";
  return (
    sign +
    Number(n).toLocaleString(undefined, {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    })
  );
}

export function formatNumber(n, digits = 4) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });
}

export function formatPrice(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  const v = Number(n);
  if (v >= 0 && v <= 1) return `${(v * 100).toFixed(1)}¢`;
  return v.toFixed(4);
}

export function formatPct(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  const v = Number(n);
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(digits)}%`;
}

export function formatDateShort(s) {
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return String(s);
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(s) {
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return String(s);
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function pnlClass(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "";
  const v = Number(n);
  if (v > 0) return "prof-pnl-pos";
  if (v < 0) return "prof-pnl-neg";
  return "";
}

export function tradeSideMeta(side) {
  switch (side) {
    case "buy":
      return { label: "Buy", className: "pd-trade-side-buy" };
    case "sell":
      return { label: "Sell", className: "pd-trade-side-sell" };
    case "settle_win":
      return { label: "Settled · Won", className: "pd-trade-side-win" };
    case "settle_loss":
      return { label: "Settled · Lost", className: "pd-trade-side-loss" };
    default:
      return { label: String(side || "—"), className: "" };
  }
}

export function initialFor(s) {
  if (!s) return "?";
  return String(s).trim().charAt(0).toUpperCase() || "?";
}
