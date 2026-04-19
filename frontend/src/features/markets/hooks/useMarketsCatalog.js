import { useEffect, useMemo, useState } from "react";
import { apiBase } from "../../../config.js";
import { buildMarketsQuery } from "../query/buildMarketsQuery.js";
import { fetchGammaMarketByQuery } from "../query/fetchGammaMarketByQuery.js";
import { fetchMarketsPage } from "../query/fetchMarketsPage.js";

export function useMarketsCatalog() {
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState("created_desc");
  const [qInput, setQInput] = useState("");
  const [q, setQ] = useState("");
  const [gammaInput, setGammaInput] = useState("");
  const [gammaQuery, setGammaQuery] = useState("");
  const [gammaMarket, setGammaMarket] = useState(null);
  const [gammaLoading, setGammaLoading] = useState(false);
  const [gammaErr, setGammaErr] = useState(null);
  const [pageSize, setPageSize] = useState(50);
  const [page, setPage] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    const t = setTimeout(() => setQ(qInput.trim()), 320);
    return () => clearTimeout(t);
  }, [qInput]);

  useEffect(() => {
    const t = setTimeout(() => setGammaQuery(gammaInput.trim()), 420);
    return () => clearTimeout(t);
  }, [gammaInput]);

  useEffect(() => {
    if (!gammaQuery) {
      setGammaMarket(null);
      setGammaErr(null);
      setGammaLoading(false);
      return;
    }
    let cancelled = false;
    setGammaLoading(true);
    setGammaErr(null);
    setGammaMarket(null);
    fetchGammaMarketByQuery(apiBase, gammaQuery)
      .then((m) => {
        if (!cancelled) {
          setGammaMarket(m);
          setGammaErr(null);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setGammaMarket(null);
          setGammaErr(e.message || String(e));
        }
      })
      .finally(() => {
        if (!cancelled) setGammaLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [gammaQuery]);

  useEffect(() => {
    setPage(0);
  }, [filter, q, pageSize, sort]);

  useEffect(() => {
    let cancelled = false;
    const qs = buildMarketsQuery(filter, q, page, pageSize, sort);
    setLoading(true);
    setErr(null);
    fetchMarketsPage(apiBase, qs)
      .then((json) => {
        if (!cancelled) setData(json);
      })
      .catch((e) => {
        if (!cancelled) {
          setData(null);
          setErr(e.message || String(e));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [filter, q, page, pageSize, sort]);

  const total = data?.total ?? 0;
  const items = data?.items ?? [];
  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);
  const pageInfo = useMemo(() => {
    const from = total === 0 ? 0 : page * pageSize + 1;
    const to = Math.min((page + 1) * pageSize, total);
    return { from, to };
  }, [page, pageSize, total]);

  return {
    filter,
    setFilter,
    sort,
    setSort,
    qInput,
    setQInput,
    gammaInput,
    setGammaInput,
    gammaMarket,
    gammaLoading,
    gammaErr,
    pageSize,
    setPageSize,
    page,
    setPage,
    loading,
    err,
    items,
    total,
    totalPages,
    pageInfo,
  };
}
