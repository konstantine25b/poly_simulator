import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext.jsx";

vi.mock("../query/authApi.js", () => ({
  fetchMe: vi.fn(),
  loginUser: vi.fn(),
  registerUser: vi.fn(),
}));

import { fetchMe, loginUser } from "../query/authApi.js";

function Probe() {
  const { isAuthenticated, booting, user, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="booting">{String(booting)}</span>
      <span data-testid="auth">{String(isAuthenticated)}</span>
      <span data-testid="email">{user?.email || ""}</span>
      <button type="button" onClick={() => login("a@test.com", "secret123")}>
        login
      </button>
      <button type="button" onClick={() => logout()}>
        logout
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("bootstraps stored session via fetchMe", async () => {
    localStorage.setItem(
      "poly.auth",
      JSON.stringify({ token: "saved-token", user: { email: "old@test.com" } }),
    );
    fetchMe.mockResolvedValue({ email: "fresh@test.com", id: 1 });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("booting")).toHaveTextContent("false"));
    expect(fetchMe).toHaveBeenCalledWith("saved-token");
    expect(screen.getByTestId("auth")).toHaveTextContent("true");
    expect(screen.getByTestId("email")).toHaveTextContent("fresh@test.com");
  });

  it("clears invalid stored session", async () => {
    localStorage.setItem("poly.auth", JSON.stringify({ token: "bad-token", user: null }));
    fetchMe.mockRejectedValue(new Error("401"));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("booting")).toHaveTextContent("false"));
    expect(screen.getByTestId("auth")).toHaveTextContent("false");
    expect(localStorage.getItem("poly.auth")).toBeNull();
  });

  it("login stores token and logout clears it", async () => {
    loginUser.mockResolvedValue({
      access_token: "new-token",
      user: { email: "x@test.com", id: 2 },
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await act(async () => {
      screen.getByText("login").click();
    });

    await waitFor(() => expect(screen.getByTestId("auth")).toHaveTextContent("true"));
    expect(localStorage.getItem("poly.auth")).toContain("new-token");

    await act(async () => {
      screen.getByText("logout").click();
    });

    expect(screen.getByTestId("auth")).toHaveTextContent("false");
    expect(localStorage.getItem("poly.auth")).toBeNull();
  });
});
