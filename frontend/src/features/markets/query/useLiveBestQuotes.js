import { useEffect, useMemo, useState } from "react";
import { marketBestBidAskWsUrl } from "./marketBestBidAskWsUrl.js";

function parseQuote(v) {
  if (v === "" || v === null || v === undefined) return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
}

export function useLiveBestQuotes(apiBase, marketRef, enabled, initialQuotes) {
  const [overrides, setOverrides] = useState(() => ({}));
  const [connectionStatus, setConnectionStatus] = useState("idle");

  const tokenKey =
    initialQuotes && initialQuotes.length
      ? initialQuotes
          .map((r) => String(r.token_id))
          .sort()
          .join("|")
      : "";

  useEffect(() => {
    setOverrides({});
  }, [marketRef]);

  useEffect(() => {
    if (!enabled || !marketRef || !tokenKey) {
      setConnectionStatus("idle");
      return undefined;
    }
    let cancelled = false;
    let opened = false;
    const url = marketBestBidAskWsUrl(apiBase, marketRef);
    setConnectionStatus("connecting");
    const ws = new WebSocket(url);
    ws.onopen = () => {
      opened = true;
      if (!cancelled) setConnectionStatus("connected");
    };
    ws.onmessage = (e) => {
      if (cancelled) return;
      let msg;
      try {
        msg = JSON.parse(e.data);
      } catch {
        return;
      }
      if (msg && typeof msg === "object" && "error" in msg) {
        setConnectionStatus("error");
        try {
          ws.close();
        } catch {}
        return;
      }
      if (msg.event_type !== "best_bid_ask" || msg.asset_id == null) return;
      const id = String(msg.asset_id);
      setOverrides((prev) => ({
        ...prev,
        [id]: {
          best_bid: parseQuote(msg.best_bid),
          best_ask: parseQuote(msg.best_ask),
        },
      }));
    };
    ws.onerror = () => {
      if (!cancelled && !opened) setConnectionStatus("error");
    };
    ws.onclose = () => {
      if (cancelled) return;
      if (!opened) setConnectionStatus("error");
      else setConnectionStatus("closed");
    };
    return () => {
      cancelled = true;
      try {
        ws.close();
      } catch {}
    };
  }, [apiBase, enabled, marketRef, tokenKey]);

  const quotes = useMemo(() => {
    const base = initialQuotes || [];
    if (!enabled) return base;
    return base.map((row) => {
      const o = overrides[String(row.token_id)];
      if (!o) return row;
      return {
        ...row,
        best_bid: o.best_bid ?? row.best_bid,
        best_ask: o.best_ask ?? row.best_ask,
      };
    });
  }, [initialQuotes, overrides, enabled]);

  return { quotes, connectionStatus };
}
