import { describe, expect, it } from "vitest";
import { buildMarketsQuery } from "./buildMarketsQuery.js";

describe("buildMarketsQuery", () => {
  it("builds active + accepting orders query", () => {
    const qs = buildMarketsQuery("active", "xqc", 2, 25, "volume_desc", true, 100, "", "", "", "");
    const p = new URLSearchParams(qs);

    expect(p.get("limit")).toBe("25");
    expect(p.get("offset")).toBe("50");
    expect(p.get("q")).toBe("xqc");
    expect(p.get("sort")).toBe("volume_desc");
    expect(p.get("active")).toBe("true");
    expect(p.get("closed")).toBe("false");
    expect(p.get("accepting_orders")).toBe("true");
    expect(p.get("min_volume")).toBe("100");
  });

  it("omits optional params when unset", () => {
    const qs = buildMarketsQuery("all", "", 0, 20, "", false, null, "", "", "", "");
    const p = new URLSearchParams(qs);

    expect(p.get("limit")).toBe("20");
    expect(p.get("offset")).toBe("0");
    expect(p.get("q")).toBeNull();
    expect(p.get("active")).toBeNull();
    expect(p.get("closed")).toBeNull();
    expect(p.get("accepting_orders")).toBeNull();
    expect(p.get("min_volume")).toBeNull();
  });

  it("maps closed filter", () => {
    const p = new URLSearchParams(buildMarketsQuery("closed", "", 0, 10, "", false, null, "", "", "", ""));
    expect(p.get("closed")).toBe("true");
    expect(p.get("active")).toBeNull();
  });
});
