const PAGE_TTL_MS = 30_000;
const DETAIL_TTL_MS = 60_000;
const GAMMA_TTL_MS = 60_000;
const MAX_PAGES = 64;
const MAX_DETAILS = 128;
const MAX_GAMMA = 64;

const pageEntries = new Map();
const detailEntries = new Map();
const gammaEntries = new Map();

function fresh(ts, ttl) {
  return Date.now() - ts < ttl;
}

function evictIfFull(map, max) {
  if (map.size < max) return;
  const oldestKey = map.keys().next().value;
  if (oldestKey !== undefined) map.delete(oldestKey);
}

function readCache(map, key, ttl) {
  const e = map.get(key);
  if (!e) return null;
  return { data: e.data, fresh: fresh(e.ts, ttl) };
}

function writeCache(map, key, data, max) {
  if (map.has(key)) map.delete(key);
  evictIfFull(map, max);
  map.set(key, { data, ts: Date.now() });
}

export function getCachedPage(qs) {
  return readCache(pageEntries, qs, PAGE_TTL_MS);
}

export function setCachedPage(qs, data) {
  writeCache(pageEntries, qs, data, MAX_PAGES);
}

export function getCachedDetail(marketRef) {
  return readCache(detailEntries, String(marketRef), DETAIL_TTL_MS);
}

export function setCachedDetail(marketRef, data) {
  writeCache(detailEntries, String(marketRef), data, MAX_DETAILS);
  const m = data?.market;
  const id = m?.id != null ? String(m.id) : null;
  const slug = m?.slug != null ? String(m.slug) : null;
  if (id && id !== String(marketRef)) writeCache(detailEntries, id, data, MAX_DETAILS);
  if (slug && slug !== String(marketRef)) writeCache(detailEntries, slug, data, MAX_DETAILS);
}

export function getCachedGammaMarket(query) {
  return readCache(gammaEntries, query.trim().toLowerCase(), GAMMA_TTL_MS);
}

export function setCachedGammaMarket(query, data) {
  writeCache(gammaEntries, query.trim().toLowerCase(), data, MAX_GAMMA);
}

export function invalidateMarketsCache() {
  pageEntries.clear();
  detailEntries.clear();
  gammaEntries.clear();
}
