import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ChatPage } from "./pages/ChatPage";

const getConversationsMock = vi.fn();
const getConversationMessagesMock = vi.fn();
const logoutMock = vi.fn();

vi.mock("./services/api", () => ({
  ApiError: class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
  conversationApi: {
    getConversations: (...args: unknown[]) =>
      getConversationsMock(...args),
    getConversationMessages: (...args: unknown[]) =>
      getConversationMessagesMock(...args),
  },
}));

vi.mock("./auth/AuthContext", () => ({
  useAuth: () => ({
    token: "test-token",
    user: {
      id: "user-1",
      email: "user@example.com",
      is_active: true,
    },
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: logoutMock,
  }),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <ChatPage />
    </MemoryRouter>,
  );
}

const conversation = {
  id: "22222222-2222-4222-8222-222222222222",
  created_at: "2026-01-02T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

describe("ChatPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getConversationsMock.mockResolvedValue({
      conversations: [],
    });
    getConversationMessagesMock.mockResolvedValue({
      conversation,
      messages: [],
    });
  });

  it("loads conversations once and renders an empty state", async () => {
    renderPage();

    expect(screen.getByRole("status")).toHaveTextContent(
      "Loading conversations…",
    );

    await waitFor(() =>
      expect(getConversationsMock).toHaveBeenCalledTimes(1),
    );

    expect(screen.getByText("No conversations yet.")).toBeInTheDocument();
    expect(getConversationMessagesMock).not.toHaveBeenCalled();
  });

  it("renders conversation-list errors", async () => {
    getConversationsMock.mockRejectedValueOnce(
      new Error("Conversation service unavailable"),
    );

    renderPage();

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Unable to load conversations.",
      ),
    );
  });

  it("selects a conversation and renders history in backend order", async () => {
    getConversationsMock.mockResolvedValueOnce({
      conversations: [conversation],
    });

    getConversationMessagesMock.mockResolvedValueOnce({
      conversation,
      messages: [
        {
          id: "message-1",
          role: "user",
          content: "first",
          sequence_number: 1,
          created_at: "2026-01-02T00:00:00Z",
        },
        {
          id: "message-2",
          role: "assistant",
          content: "second",
          sequence_number: 2,
          created_at: "2026-01-02T00:01:00Z",
        },
      ],
    });

    renderPage();

    await waitFor(() =>
      expect(
        screen.getByRole("button", {
          name: conversation.id,
        }),
      ).toBeInTheDocument(),
    );

    fireEvent.click(
      screen.getByRole("button", { name: conversation.id }),
    );

    await waitFor(() =>
      expect(getConversationMessagesMock).toHaveBeenCalledWith(
        "test-token",
        conversation.id,
      ),
    );

    expect(screen.getByText("first")).toBeInTheDocument();
    expect(screen.getByText("second")).toBeInTheDocument();

    const contents = screen.getAllByText(/first|second/);
    expect(contents[0]).toHaveTextContent("first");
    expect(contents[1]).toHaveTextContent("second");
  });

  it("renders an empty history", async () => {
    getConversationsMock.mockResolvedValueOnce({
      conversations: [conversation],
    });

    renderPage();

    fireEvent.click(
      await screen.findByRole("button", { name: conversation.id }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("This conversation has no messages yet."),
      ).toBeInTheDocument(),
    );
  });

  it("renders history errors", async () => {
    getConversationsMock.mockResolvedValueOnce({
      conversations: [conversation],
    });
    getConversationMessagesMock.mockRejectedValueOnce(
      new Error("History unavailable"),
    );

    renderPage();

    fireEvent.click(
      await screen.findByRole("button", { name: conversation.id }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("Unable to load conversation history."),
      ).toBeInTheDocument(),
    );
  });

  it("new conversation clears the active history without making an API request", async () => {
    getConversationsMock.mockResolvedValueOnce({
      conversations: [conversation],
    });
    getConversationMessagesMock.mockResolvedValueOnce({
      conversation,
      messages: [
        {
          id: "message-1",
          role: "user",
          content: "existing message",
          sequence_number: 1,
          created_at: "2026-01-02T00:00:00Z",
        },
      ],
    });

    renderPage();

    fireEvent.click(
      await screen.findByRole("button", { name: conversation.id }),
    );

    await waitFor(() =>
      expect(screen.getByText("existing message")).toBeInTheDocument(),
    );

    const callCountBeforeNew = getConversationMessagesMock.mock.calls.length;

    fireEvent.click(
      screen.getByRole("button", { name: "New conversation" }),
    );

    expect(
      screen.getByText("Start a new conversation"),
    ).toBeInTheDocument();
    expect(screen.queryByText("existing message")).not.toBeInTheDocument();
    expect(getConversationMessagesMock).toHaveBeenCalledTimes(
      callCountBeforeNew,
    );
  });

  it("does not expose or call chat submission in batch 1", async () => {
    renderPage();

    await waitFor(() =>
      expect(getConversationsMock).toHaveBeenCalledTimes(1),
    );

    const textarea = screen.getByRole("textbox", { name: "Message" });
    const sendButton = screen.getByRole("button", { name: "Send" });

    expect(textarea).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });
});
