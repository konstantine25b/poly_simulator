import { useCallback, useEffect, useState } from "react";
import { fetchPortfolios } from "../query/portfoliosApi.js";

function visibleToUser(portfolios, userId, isAdmin) {
  if (isAdmin) return portfolios;
  if (userId === null || userId === undefined) return portfolios;
  return portfolios.filter((p) => Number(p.user_id) === Number(userId));
}

export function useUserPortfolios(token, userId, isAdmin) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr(null);
    try {
      const all = await fetchPortfolios(token);
      setItems(visibleToUser(all, userId, isAdmin));
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [token, userId, isAdmin]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setErr(null);
      try {
        const all = await fetchPortfolios(token);
        if (!cancelled) setItems(visibleToUser(all, userId, isAdmin));
      } catch (e) {
        if (!cancelled) setErr(e.message || String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, userId, isAdmin]);

  return { items, loading, err, refresh };
}
