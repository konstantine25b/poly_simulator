import { useEffect, useState } from "react";
import { fetchMarketDetail } from "./fetchMarketDetail.js";
import { useLiveBestQuotes } from "./useLiveBestQuotes.js";

export function useLiveMarketQuotes(apiBase, marketRef) {
  const [initialQuotes, setInitialQuotes] = useState(null);
  const [closed, setClosed] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!marketRef) return undefined;
    let cancelled = false;
    setErr(null);
    setInitialQuotes(null);
    setClosed(false);
    fetchMarketDetail(apiBase, marketRef)
      .then((d) => {
        if (cancelled) return;
        setInitialQuotes(d.best_quotes || []);
        setClosed(Boolean(d.closed));
      })
      .catch((e) => {
        if (!cancelled) setErr(e.message || String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [apiBase, marketRef]);

  const wsEnabled = Boolean(initialQuotes && initialQuotes.length && !closed);
  const { quotes, connectionStatus } = useLiveBestQuotes(
    apiBase,
    marketRef,
    wsEnabled,
    initialQuotes || [],
  );

  return {
    quotes: quotes || [],
    connectionStatus,
    closed,
    err,
    ready: initialQuotes !== null,
  };
}
