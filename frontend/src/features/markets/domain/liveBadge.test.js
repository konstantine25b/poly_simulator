import { describe, expect, it } from "vitest";
import { isMarketPastEnd, parseMarketEndMs, shouldShowLiveBadge } from "./liveBadge.js";

describe("liveBadge", () => {
  it("parses endDateIso as end of UTC day", () => {
    const ms = parseMarketEndMs({ endDateIso: "2026-05-31" });
    expect(ms).toBe(Date.parse("2026-05-31T23:59:59.999Z"));
  });

  it("detects market past end", () => {
    const market = { endDateIso: "2020-01-01", active: 1, closed: 0 };
    expect(isMarketPastEnd(market, Date.parse("2026-01-01T00:00:00Z"))).toBe(true);
  });

  it("hides live badge when closed or past end", () => {
    const open = { active: 1, closed: 0, endDateIso: "2099-01-01" };
    const closed = { active: 1, closed: 1, endDateIso: "2099-01-01" };
    const expired = { active: 1, closed: 0, endDateIso: "2020-01-01" };
    const now = Date.parse("2026-01-01T00:00:00Z");

    expect(shouldShowLiveBadge(open, now)).toBe(true);
    expect(shouldShowLiveBadge(closed, now)).toBe(false);
    expect(shouldShowLiveBadge(expired, now)).toBe(false);
  });
});
