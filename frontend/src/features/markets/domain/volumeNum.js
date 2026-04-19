import { field } from "./rowField.js";

export function readVolumeNum(row) {
  const raw = field(row, "volumeNum");
  if (raw === undefined || raw === null || raw === "") return null;
  const n = Number(raw);
  return Number.isNaN(n) ? null : n;
}
