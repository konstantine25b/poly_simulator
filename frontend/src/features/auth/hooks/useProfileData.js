import { useCallback, useEffect, useRef, useState } from "react";
import {
  createPortfolio,
  deletePortfolio,
  fetchAdminUsers,
  fetchPortfolioSummary,
  fetchPortfolios,
} from "../query/portfoliosApi.js";
import {
  getCachedList,
  invalidateDetail,
  setCachedList,
  updateCachedList,
} from "../query/portfoliosCache.js";

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
  const cached = token ? getCachedList(userId, isAdmin) : null;
  const [items, setItems] = useState(cached?.data ?? []);
  const [loading, setLoading] = useState(!cached);
  const [err, setErr] = useState(null);
  const [creating, setCreating] = useState(false);
  const inflight = useRef(false);

  const reload = useCallback(
    async (showSpinner) => {
      if (!token) return;
      if (inflight.current) return;
      inflight.current = true;
      if (showSpinner) setLoading(true);
      setErr(null);
      try {
        const data = await loadPortfoliosWithSummaries(token, userId, isAdmin);
        setItems(data);
        setCachedList(userId, isAdmin, data);
      } catch (e) {
        setErr(e.message || String(e));
      } finally {
        inflight.current = false;
        setLoading(false);
      }
    },
    [token, userId, isAdmin],
  );

  const refresh = useCallback(() => reload(true), [reload]);

  useEffect(() => {
    if (!token) return;
    const c = getCachedList(userId, isAdmin);
    if (c) {
      setItems(c.data);
      setLoading(false);
      if (c.fresh) return;
    }
    reload(!c);
  }, [token, userId, isAdmin, reload]);

  const create = useCallback(
    async (body) => {
      if (!token) return null;
      setCreating(true);
      setErr(null);
      try {
        const created = await createPortfolio(token, body || {});
        await reload(false);
        return created;
      } finally {
        setCreating(false);
      }
    },
    [token, reload],
  );

  const remove = useCallback(
    async (portfolioId) => {
      if (!token || portfolioId === undefined || portfolioId === null) return null;
      const result = await deletePortfolio(token, portfolioId);
      const target = Number(portfolioId);
      setItems((prev) => prev.filter((p) => Number(p.id) !== target));
      updateCachedList(userId, isAdmin, (list) =>
        list.filter((p) => Number(p.id) !== target),
      );
      invalidateDetail(portfolioId);
      return result;
    },
    [token, userId, isAdmin],
  );

  return { items, loading, err, creating, create, remove, refresh };
}
