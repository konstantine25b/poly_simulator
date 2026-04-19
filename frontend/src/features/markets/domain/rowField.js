export function field(row, name) {
  if (row == null) return null;
  const v = row[name];
  if (v !== undefined && v !== null && v !== "") return v;
  const low = name.toLowerCase();
  if (row[low] !== undefined && row[low] !== null && row[low] !== "") return row[low];
  return null;
}

export function parseJsonArray(v) {
  if (Array.isArray(v)) return v;
  if (typeof v === "string") {
    try {
      const x = JSON.parse(v);
      return Array.isArray(x) ? x : [];
    } catch {
      return [];
    }
  }
  return [];
}
