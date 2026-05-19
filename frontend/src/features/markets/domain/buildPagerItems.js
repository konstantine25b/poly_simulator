export function buildPagerItems(current, total, siblingCount = 1) {
  if (total <= 0) return [];
  if (total === 1) return [0];
  const pages = new Set([0, total - 1]);
  const lo = Math.max(0, current - siblingCount);
  const hi = Math.min(total - 1, current + siblingCount);
  for (let i = lo; i <= hi; i += 1) pages.add(i);
  const sorted = [...pages].sort((a, b) => a - b);
  const items = [];
  let prev = null;
  for (const p of sorted) {
    if (prev !== null && p - prev > 1) items.push("ellipsis");
    items.push(p);
    prev = p;
  }
  return items;
}
