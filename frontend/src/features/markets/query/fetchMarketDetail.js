export async function fetchMarketDetail(apiBase, marketRef) {
  const enc = encodeURIComponent(marketRef);
  const res = await fetch(`${apiBase}/markets/${enc}/detail`);
  if (res.status === 404) {
    throw new Error("Market not found.");
  }
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }
  return res.json();
}
