const LIST_TTL_MS = 30_000;
const DETAIL_TTL_MS = 30_000;

const listEntries = new Map();
const detailEntries = new Map();

function listKey(userId, isAdmin) {
  return `${isAdmin ? "admin" : "user"}:${userId ?? ""}`;
}

function detailKey(portfolioId) {
  return String(portfolioId);
}

function fresh(ts, ttl) {
  return Date.now() - ts < ttl;
}

export function getCachedList(userId, isAdmin) {
  const e = listEntries.get(listKey(userId, isAdmin));
  if (!e) return null;
  return { data: e.data, fresh: fresh(e.ts, LIST_TTL_MS) };
}

export function setCachedList(userId, isAdmin, data) {
  listEntries.set(listKey(userId, isAdmin), { data, ts: Date.now() });
}

export function updateCachedList(userId, isAdmin, updater) {
  const key = listKey(userId, isAdmin);
  const e = listEntries.get(key);
  if (!e) return;
  const next = updater(e.data);
  if (next === undefined || next === null) return;
  listEntries.set(key, { data: next, ts: e.ts });
}

export function invalidateList() {
  listEntries.clear();
}

export function getCachedDetail(portfolioId) {
  const e = detailEntries.get(detailKey(portfolioId));
  if (!e) return null;
  return { data: e.data, fresh: fresh(e.ts, DETAIL_TTL_MS) };
}

export function setCachedDetail(portfolioId, data) {
  detailEntries.set(detailKey(portfolioId), { data, ts: Date.now() });
}

export function invalidateDetail(portfolioId) {
  if (portfolioId === undefined || portfolioId === null) {
    detailEntries.clear();
    return;
  }
  detailEntries.delete(detailKey(portfolioId));
}

export function findPortfolioInListCaches(portfolioId) {
  const target = Number(portfolioId);
  for (const entry of listEntries.values()) {
    const list = entry.data;
    if (!Array.isArray(list)) continue;
    const found = list.find((p) => Number(p.id) === target);
    if (found) return found;
  }
  return null;
}
