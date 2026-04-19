export function buildMarketsQuery(filter, q, page, pageSize, sort) {
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
  return p.toString();
}
