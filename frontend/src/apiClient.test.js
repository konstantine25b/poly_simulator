import { afterEach, describe, expect, it, vi } from "vitest";
import { apiGet, apiPost, extractErrorMessage } from "./apiClient.js";

describe("extractErrorMessage", () => {
  it("returns API detail string", () => {
    expect(extractErrorMessage({ detail: "invalid token" }, 401)).toBe("invalid token");
  });

  it("formats validation array", () => {
    const data = {
      detail: [{ loc: ["body", "email"], msg: "invalid email" }],
    };
    expect(extractErrorMessage(data, 422)).toBe("email: invalid email");
  });

  it("falls back to status defaults", () => {
    expect(extractErrorMessage(null, 401)).toBe("Invalid email or password.");
    expect(extractErrorMessage(null, 409)).toBe("Email already registered.");
    expect(extractErrorMessage(null, 500)).toBe("Server error. Please try again.");
    expect(extractErrorMessage(null, 418)).toBe("Request failed (418)");
  });
});

describe("apiClient requests", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("apiGet sends bearer token and returns JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const data = await apiGet("/auth/me", "tok-abc");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/me",
      expect.objectContaining({
        method: "GET",
        headers: { Authorization: "Bearer tok-abc" },
      }),
    );
    expect(data).toEqual({ id: 1 });
  });

  it("apiPost throws parsed API error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: "insufficient balance" }),
      }),
    );

    await expect(apiPost("/portfolios/1/bet", { shares: 1 }, "tok")).rejects.toThrow(
      "insufficient balance",
    );
  });

  it("surfaces network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(apiGet("/health")).rejects.toThrow("Network error: offline");
  });
});
