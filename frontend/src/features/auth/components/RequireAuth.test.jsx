import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { RequireAuth } from "./RequireAuth.jsx";

vi.mock("../context/AuthContext.jsx", () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from "../context/AuthContext.jsx";

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <div>Protected profile</div>
            </RequireAuth>
          }
        />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireAuth", () => {
  it("redirects unauthenticated users to login", () => {
    useAuth.mockReturnValue({ isAuthenticated: false, booting: false });
    renderAt("/profile");
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    useAuth.mockReturnValue({ isAuthenticated: true, booting: false });
    renderAt("/profile");
    expect(screen.getByText("Protected profile")).toBeInTheDocument();
  });

  it("renders nothing while booting", () => {
    useAuth.mockReturnValue({ isAuthenticated: false, booting: true });
    const { container } = renderAt("/profile");
    expect(container).toBeEmptyDOMElement();
  });
});
