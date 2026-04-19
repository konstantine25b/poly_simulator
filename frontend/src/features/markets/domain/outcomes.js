import { field, parseJsonArray } from "./rowField.js";

export function outcomeCount(market) {
  return parseJsonArray(field(market, "outcomes")).length;
}
