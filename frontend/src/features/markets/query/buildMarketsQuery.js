export function buildMarketsQuery(
  filter,
  q,
  page,
  pageSize,
  sort,
  acceptingOrdersOnly,
  minVolume,
) {
  const p = new URLSearchParams();
  p.set("limit", String(pageSize));
  p.set("offset", String(page * pageSize));
  if (sort) p.set("sort", sort);
  if (q) p.set("q", q);
  if (filter === "active") {
    p.set("active", "true");
    p.set("closed", "false");
  } else if (filter === "closed") {
    p.set("closed", "true");
  }
  if (acceptingOrdersOnly) p.set("accepting_orders", "true");
  if (minVolume != null && minVolume > 0) p.set("min_volume", String(minVolume));
  return p.toString();
}
