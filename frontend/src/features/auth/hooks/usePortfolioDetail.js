import { useCallback, useEffect, useState } from "react";
import {
  fetchPortfolioPositions,
  fetchPortfolioSummary,
  fetchPortfolioTrades,
} from "../query/portfoliosApi.js";

async function loadAll(token, portfolioRef) {
  const [summary, positions, trades] = await Promise.all([
    fetchPortfolioSummary(token, portfolioRef),
    fetchPortfolioPositions(token, portfolioRef),
    fetchPortfolioTrades(token, portfolioRef),
  ]);
  return { summary, positions, trades };
}

export function usePortfolioDetail(token, portfolioRef) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const refresh = useCallback(async () => {
    if (!token || !portfolioRef) return;
    setLoading(true);
    setErr(null);
    try {
      setData(await loadAll(token, portfolioRef));
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [token, portfolioRef]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!token || !portfolioRef) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setErr(null);
      try {
        const next = await loadAll(token, portfolioRef);
        if (!cancelled) setData(next);
      } catch (e) {
        if (!cancelled) setErr(e.message || String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, portfolioRef]);

  return { data, loading, err, refresh };
}
