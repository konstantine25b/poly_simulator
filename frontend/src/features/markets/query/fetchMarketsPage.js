export async function fetchMarketsPage(apiBase, queryString) {
  const res = await fetch(`${apiBase}/db/markets?${queryString}`);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }
  return res.json();
}
