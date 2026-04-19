export function marketBestBidAskWsUrl(apiBase, marketRef) {
  const path = `/ws/markets/${encodeURIComponent(marketRef)}/best-bid-ask`;
  if (apiBase.startsWith("http://")) {
    const rest = apiBase.slice("http://".length).replace(/\/$/, "");
    return `ws://${rest}${path}`;
  }
  if (apiBase.startsWith("https://")) {
    const rest = apiBase.slice("https://".length).replace(/\/$/, "");
    return `wss://${rest}${path}`;
  }
  if (import.meta.env.DEV && apiBase === "/api") {
    return `ws://127.0.0.1:8000${path}`;
  }
  const proto = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = typeof window !== "undefined" ? window.location.host : "";
  const base = (apiBase || "").replace(/\/$/, "");
  return `${proto}//${host}${base}${path}`;
}
