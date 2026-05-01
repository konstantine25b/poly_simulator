import { useEffect } from "react";
import { useLiveMarketQuotes } from "./useLiveMarketQuotes.js";

export function LiveMarketQuoteSub({ apiBase, marketRef, onChange }) {
  const { quotes, connectionStatus, closed, err, ready } = useLiveMarketQuotes(
    apiBase,
    marketRef,
  );

  useEffect(() => {
    if (!onChange) return;
    onChange(marketRef, { quotes, connectionStatus, closed, err, ready });
  }, [marketRef, quotes, connectionStatus, closed, err, ready, onChange]);

  return null;
}
