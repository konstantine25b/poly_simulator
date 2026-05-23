import { useEffect, useMemo, useRef, useState } from "react";
import { apiBase } from "../../../config.js";
import { usePhoneLayout } from "../../../hooks/usePhoneLayout.js";
import { buildMarketsQuery } from "../query/buildMarketsQuery.js";
import { fetchGammaMarketByQuery } from "../query/fetchGammaMarketByQuery.js";
import { fetchMarketsPage } from "../query/fetchMarketsPage.js";
import {
  getCachedGammaMarket,
  getCachedPage,
  setCachedGammaMarket,
  setCachedPage,
} from "../query/marketsCache.js";

const STATE_KEY = "polyptrade.marketsCatalog.v1";

function readPersisted() {
  try {
    const raw = sessionStorage.getItem(STATE_KEY);
    if (!raw) return null;
    const v = JSON.parse(raw);
    return v && typeof v === "object" ? v : null;
  } catch {
    return null;
  }
}

function writePersisted(state) {
  try {
    sessionStorage.setItem(STATE_KEY, JSON.stringify(state));
  } catch {}
}

export function useMarketsCatalog() {
  const isPhone = usePhoneLayout();
  const persisted = useRef(readPersisted()).current || {};
  const [filter, setFilter] = useState(persisted.filter ?? "all");
  const [sort, setSort] = useState(persisted.sort ?? "created_desc");
  const [acceptingOrdersOnly, setAcceptingOrdersOnly] = useState(
    persisted.acceptingOrdersOnly ?? false,
  );
  const [minVolumeInput, setMinVolumeInput] = useState(persisted.minVolumeInput ?? "");
  const [minVolume, setMinVolume] = useState(persisted.minVolume ?? null);
  const [startDateFrom, setStartDateFrom] = useState(persisted.startDateFrom ?? "");
  const [startDateTo, setStartDateTo] = useState(persisted.startDateTo ?? "");
  const [endDateFrom, setEndDateFrom] = useState(persisted.endDateFrom ?? "");
  const [endDateTo, setEndDateTo] = useState(persisted.endDateTo ?? "");
  const [qInput, setQInput] = useState(persisted.qInput ?? "");
  const [q, setQ] = useState(persisted.q ?? "");
  const [gammaInput, setGammaInput] = useState(persisted.gammaInput ?? "");
  const [gammaQuery, setGammaQuery] = useState(persisted.gammaQuery ?? "");
  const [gammaMarket, setGammaMarket] = useState(null);
  const [gammaLoading, setGammaLoading] = useState(false);
  const [gammaErr, setGammaErr] = useState(null);
  const [pageSizeDesktop, setPageSizeDesktop] = useState(persisted.pageSizeDesktop ?? 50);
  const pageSize = isPhone ? 10 : pageSizeDesktop;
  const [page, setPage] = useState(persisted.page ?? 0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasFreshData, setHasFreshData] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    const t = setTimeout(() => setQ(qInput.trim()), 320);
    return () => clearTimeout(t);
  }, [qInput]);

  useEffect(() => {
    const t = setTimeout(() => {
      const s = minVolumeInput.trim();
      if (!s) {
        setMinVolume(null);
        return;
      }
      const n = Number(s);
      setMinVolume(Number.isFinite(n) && n >= 0 ? n : null);
    }, 320);
    return () => clearTimeout(t);
  }, [minVolumeInput]);

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
    const cached = getCachedGammaMarket(gammaQuery);
    if (cached) {
      setGammaMarket(cached.data);
      setGammaErr(null);
      setGammaLoading(false);
      if (cached.fresh) return;
    } else {
      setGammaLoading(true);
      setGammaErr(null);
      setGammaMarket(null);
    }
    fetchGammaMarketByQuery(apiBase, gammaQuery)
      .then((m) => {
        if (cancelled) return;
        setGammaMarket(m);
        setGammaErr(null);
        setCachedGammaMarket(gammaQuery, m);
      })
      .catch((e) => {
        if (cancelled) return;
        if (!cached) setGammaMarket(null);
        setGammaErr(e.message || String(e));
      })
      .finally(() => {
        if (!cancelled) setGammaLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [gammaQuery]);

  const skipResetRef = useRef(true);
  useEffect(() => {
    if (skipResetRef.current) {
      skipResetRef.current = false;
      return;
    }
    setPage(0);
  }, [
    filter,
    q,
    pageSize,
    sort,
    acceptingOrdersOnly,
    minVolume,
    startDateFrom,
    startDateTo,
    endDateFrom,
    endDateTo,
  ]);

  useEffect(() => {
    let cancelled = false;
    const qs = buildMarketsQuery(
      filter,
      q,
      page,
      pageSize,
      sort,
      acceptingOrdersOnly,
      minVolume,
      startDateFrom,
      startDateTo,
      endDateFrom,
      endDateTo,
    );
    const cached = getCachedPage(qs);
    if (cached) {
      setData(cached.data);
      setErr(null);
      setLoading(false);
      setHasFreshData(true);
      if (cached.fresh) return;
    } else {
      setLoading(true);
      setErr(null);
      setHasFreshData(false);
    }
    fetchMarketsPage(apiBase, qs)
      .then((json) => {
        if (cancelled) return;
        setData(json);
        setErr(null);
        setHasFreshData(true);
        setCachedPage(qs, json);
      })
      .catch((e) => {
        if (cancelled) return;
        if (!cached) setData(null);
        setErr(e.message || String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [
    filter,
    q,
    page,
    pageSize,
    sort,
    acceptingOrdersOnly,
    minVolume,
    startDateFrom,
    startDateTo,
    endDateFrom,
    endDateTo,
  ]);

  useEffect(() => {
    writePersisted({
      filter,
      sort,
      acceptingOrdersOnly,
      minVolumeInput,
      minVolume,
      startDateFrom,
      startDateTo,
      endDateFrom,
      endDateTo,
      qInput,
      q,
      gammaInput,
      gammaQuery,
      pageSizeDesktop,
      page,
    });
  }, [
    filter,
    sort,
    acceptingOrdersOnly,
    minVolumeInput,
    minVolume,
    startDateFrom,
    startDateTo,
    endDateFrom,
    endDateTo,
    qInput,
    q,
    gammaInput,
    gammaQuery,
    pageSizeDesktop,
    page,
  ]);

  const showSkeletons = loading && !hasFreshData;
  const total = data?.total ?? 0;
  const items = showSkeletons ? [] : (data?.items ?? []);
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
    acceptingOrdersOnly,
    setAcceptingOrdersOnly,
    minVolumeInput,
    setMinVolumeInput,
    startDateFrom,
    setStartDateFrom,
    startDateTo,
    setStartDateTo,
    endDateFrom,
    setEndDateFrom,
    endDateTo,
    setEndDateTo,
    qInput,
    setQInput,
    gammaInput,
    setGammaInput,
    gammaMarket,
    gammaLoading,
    gammaErr,
    pageSize,
    setPageSize: setPageSizeDesktop,
    page,
    setPage,
    loading,
    showSkeletons,
    err,
    items,
    total,
    totalPages,
    pageInfo,
  };
}
