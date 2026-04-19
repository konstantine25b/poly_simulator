export function formatUsdCompact(n) {
  if (n == null) return null;
  const x = Number(n);
  if (Number.isNaN(x)) return null;
  if (x >= 1e9) return `$${(x / 1e9).toFixed(1)}B`;
  if (x >= 1e6) return `$${(x / 1e6).toFixed(1)}M`;
  if (x >= 1e3) return `$${(x / 1e3).toFixed(0)}K`;
  return `$${x.toFixed(0)}`;
}

export function formatDate(raw) {
  if (raw == null || raw === "") return null;
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return null;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(d);
}

export function formatOutcomeOdds(raw) {
  const n = Number(raw);
  if (Number.isNaN(n)) return null;
  const p = n >= 0 && n <= 1 ? n * 100 : n;
  if (p >= 10 || p === Math.floor(p)) return `${Math.round(p)}%`;
  return `${p.toFixed(1)}%`;
}
