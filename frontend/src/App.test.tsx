import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "./App";
import { TOKEN_STORAGE_KEY } from "./auth/AuthContext";

const meMock = vi.fn();
const listDocumentsMock = vi.fn();

vi.mock("./services/documents", () => ({
  documentsApi: {
    list: (...args: unknown[]) => listDocumentsMock(...args),
    upload: vi.fn(),
  },
}));

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
    listDocumentsMock.mockReset();
    listDocumentsMock.mockResolvedValue([]);
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

  it("exposes the authenticated Chat route", async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, "test-token");

    meMock.mockResolvedValue({
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    });

    render(
      <MemoryRouter initialEntries={["/app/chat"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Chat" }),
    ).toBeInTheDocument();
  });


  it("renders the authenticated application shell and primary navigation", async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, "test-token");

    meMock.mockResolvedValue({
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    });

    listDocumentsMock.mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("navigation", {
        name: "Primary",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: "Chat" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: "Documents" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: /New Chat/ }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Log out from application" }),
    ).toBeInTheDocument();

    const banners = screen.getAllByRole("banner");

    expect(banners.length).toBeGreaterThan(0);
    expect(
      within(banners[0]).getByText("ahmed@example.com"),
    ).toBeInTheDocument();
  });

  it("marks the active route in the shared navigation", async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, "test-token");

    meMock.mockResolvedValue({
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    });

    listDocumentsMock.mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={["/app/chat"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Chat" });

    expect(
      screen.getByRole("link", { name: "Chat" }),
    ).toHaveAttribute("aria-current", "page");

    expect(
      screen.getByRole("link", { name: "Documents" }),
    ).not.toHaveAttribute("aria-current", "page");
  });

  it("navigates from the shared sidebar to Chat", async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, "test-token");

    meMock.mockResolvedValue({
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    });

    listDocumentsMock.mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Dashboard" });

    fireEvent.click(
      screen.getByRole("link", { name: "Chat" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Chat" }),
    ).toBeInTheDocument();
  });

  it("keeps navigation keyboard accessible", async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, "test-token");

    meMock.mockResolvedValue({
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    });

    listDocumentsMock.mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("navigation", {
      name: "Primary",
    });

    const chatLink = screen.getByRole("link", {
      name: "Chat",
    });

    chatLink.focus();

    expect(document.activeElement).toBe(chatLink);
  });

  it("logs out from the shared shell", async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, "test-token");

    meMock.mockResolvedValue({
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    });

    listDocumentsMock.mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByRole("heading", {
      name: "Dashboard",
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Log out from application" }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "Sign in",
      }),
    ).toBeInTheDocument();
  });

  it("restores an authenticated user from the persisted token", async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, "test-token");

    meMock.mockResolvedValue({
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    });

    listDocumentsMock.mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <App />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", {
          name: "Dashboard",
        }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getAllByText(/ahmed@example.com/).length,
    ).toBeGreaterThan(0);

    expect(meMock).toHaveBeenCalledWith("test-token");
  });
});
