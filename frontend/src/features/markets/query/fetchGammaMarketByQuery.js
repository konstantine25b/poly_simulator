export async function fetchGammaMarketByQuery(apiBase, query) {
  const enc = encodeURIComponent(query.trim());
  const res = await fetch(`${apiBase}/markets/${enc}/live`);
  if (res.status === 404) {
    throw new Error("No market found on Polymarket for that id or slug.");
  }
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }
  return res.json();
}
