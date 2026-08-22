import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "./App";
import { TOKEN_STORAGE_KEY } from "./auth/AuthContext";

const meMock = vi.fn();

vi.mock("./services/api", () => ({
  authApi: {
    me: (...args: unknown[]) => meMock(...args),
    login: vi.fn(),
    register: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

describe("frontend authentication foundation", () => {
  beforeEach(() => {
    localStorage.clear();
    meMock.mockReset();
  });

  it("redirects the root route to login", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
  });

  it("renders the register page", async () => {
    render(
      <MemoryRouter initialEntries={["/register"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Create account" }),
    ).toBeInTheDocument();
  });

  it("protects the application shell without authentication", async () => {
    render(
      <MemoryRouter initialEntries={["/app"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
  });

  it("restores an authenticated user from the persisted token", async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, "test-token");

    meMock.mockResolvedValue({
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <App />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", {
          name: "Authenticated application shell",
        }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(/ahmed@example.com/),
    ).toBeInTheDocument();

    expect(meMock).toHaveBeenCalledWith("test-token");
  });
});
