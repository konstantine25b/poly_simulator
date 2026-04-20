import { useCallback, useEffect, useState } from "react";
import {
  createPortfolio,
  deletePortfolio,
  fetchAdminUsers,
  fetchPortfolioSummary,
  fetchPortfolios,
} from "../query/portfoliosApi.js";

function filterForViewer(portfolios, userId, isAdmin) {
  if (isAdmin) return portfolios;
  if (userId === null || userId === undefined) return portfolios;
  return portfolios.filter((p) => Number(p.user_id) === Number(userId));
}

async function loadUserIndex(token, isAdmin) {
  if (!isAdmin) return null;
  try {
    const users = await fetchAdminUsers(token);
    const map = new Map();
    for (const u of users) map.set(Number(u.id), u);
    return map;
  } catch {
    return null;
  }
}

async function loadPortfoliosWithSummaries(token, userId, isAdmin) {
  const [all, userIndex] = await Promise.all([fetchPortfolios(token), loadUserIndex(token, isAdmin)]);
  const visible = filterForViewer(all, userId, isAdmin);
  const summaries = await Promise.all(
    visible.map((p) => fetchPortfolioSummary(token, p.id).catch(() => null)),
  );
  return visible.map((p, i) => {
    const owner = userIndex ? userIndex.get(Number(p.user_id)) : null;
    return {
      ...p,
      summary: summaries[i],
      owner_email: owner?.email ?? null,
    };
  });
}

export function useProfileData(token, userId, isAdmin) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [creating, setCreating] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr(null);
    try {
      const data = await loadPortfoliosWithSummaries(token, userId, isAdmin);
      setItems(data);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [token, userId, isAdmin]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!token) return;
      try {
        const data = await loadPortfoliosWithSummaries(token, userId, isAdmin);
        if (!cancelled) setItems(data);
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

  const create = useCallback(
    async (body) => {
      if (!token) return null;
      setCreating(true);
      setErr(null);
      try {
        const created = await createPortfolio(token, body || {});
        await refresh();
        return created;
      } finally {
        setCreating(false);
      }
    },
    [token, refresh],
  );

  const remove = useCallback(
    async (portfolioId) => {
      if (!token || portfolioId === undefined || portfolioId === null) return null;
      const result = await deletePortfolio(token, portfolioId);
      setItems((prev) => prev.filter((p) => Number(p.id) !== Number(portfolioId)));
      return result;
    },
    [token],
  );

  return { items, loading, err, creating, create, remove, refresh };
}
