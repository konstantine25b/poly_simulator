import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchPortfolioPositions,
  fetchPortfolioSummary,
  fetchPortfolioTrades,
} from "../query/portfoliosApi.js";
import {
  findPortfolioInListCaches,
  getCachedDetail,
  setCachedDetail,
} from "../query/portfoliosCache.js";

async function loadAll(token, portfolioRef) {
  const [summary, positions, trades] = await Promise.all([
    fetchPortfolioSummary(token, portfolioRef),
    fetchPortfolioPositions(token, portfolioRef),
    fetchPortfolioTrades(token, portfolioRef),
  ]);
  return { summary, positions, trades };
}

function seedFromListCache(portfolioRef) {
  const found = findPortfolioInListCaches(portfolioRef);
  if (!found || !found.summary) return null;
  return { summary: found.summary, positions: [], trades: [] };
}

export function usePortfolioDetail(token, portfolioRef) {
  const initial = (() => {
    if (!portfolioRef) return { data: null, fromCache: false };
    const c = getCachedDetail(portfolioRef);
    if (c) return { data: c.data, fromCache: true, fresh: c.fresh };
    const seed = seedFromListCache(portfolioRef);
    return { data: seed, fromCache: Boolean(seed), fresh: false };
  })();

  const [data, setData] = useState(initial.data);
  const [loading, setLoading] = useState(!initial.fromCache);
  const [err, setErr] = useState(null);
  const inflight = useRef(false);

  const reload = useCallback(
    async (showSpinner) => {
      if (!token || !portfolioRef) return;
      if (inflight.current) return;
      inflight.current = true;
      if (showSpinner) setLoading(true);
      setErr(null);
      try {
        const next = await loadAll(token, portfolioRef);
        setData(next);
        setCachedDetail(portfolioRef, next);
      } catch (e) {
        setErr(e.message || String(e));
      } finally {
        inflight.current = false;
        setLoading(false);
      }
    },
    [token, portfolioRef],
  );

  const refresh = useCallback(() => reload(true), [reload]);

  useEffect(() => {
    if (!token || !portfolioRef) {
      setLoading(false);
      return;
    }
    const c = getCachedDetail(portfolioRef);
    if (c) {
      setData(c.data);
      setLoading(false);
      if (c.fresh) return;
      reload(false);
      return;
    }
    const seed = seedFromListCache(portfolioRef);
    if (seed) {
      setData(seed);
      setLoading(false);
      reload(false);
      return;
    }
    reload(true);
  }, [token, portfolioRef, reload]);

  return { data, loading, err, refresh };
}
