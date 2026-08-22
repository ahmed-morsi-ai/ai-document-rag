import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ChatPage } from "./pages/ChatPage";
import type { ConversationMessage } from "./types/conversations";

const getConversationsMock = vi.fn();
const getConversationMessagesMock = vi.fn();
const sendMessageMock = vi.fn();
const logoutMock = vi.fn();

vi.mock("./services/api", () => ({
  ApiError: class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
  chatApi: {
    sendMessage: (...args: unknown[]) =>
      sendMessageMock(...args),
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
    vi.resetAllMocks();
    sendMessageMock.mockResolvedValue({
      query: "hello",
      answer: "hello answer",
    });
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

  it("does not send empty or whitespace-only messages", async () => {
    renderPage();

    await waitFor(() =>
      expect(getConversationsMock).toHaveBeenCalledTimes(1),
    );

    const textarea = screen.getByRole("textbox", {
      name: "Message",
    });
    const sendButton = screen.getByRole("button", {
      name: "Send",
    });

    await act(async () => {
      fireEvent.change(textarea, {
        target: { value: "" },
      });
    });
    expect(sendButton).toBeDisabled();

    await act(async () => {
      fireEvent.change(textarea, {
        target: { value: "   " },
      });
    });
    expect(sendButton).toBeDisabled();

    expect(sendMessageMock).not.toHaveBeenCalled();
  });

  it("sends the active conversation id for an existing conversation", async () => {
    getConversationsMock.mockResolvedValueOnce({
      conversations: [conversation],
    });

    getConversationMessagesMock.mockResolvedValue({
      conversation,
      messages: [],
    });

    renderPage();

    fireEvent.click(
      await screen.findByRole("button", {
        name: conversation.id,
      }),
    );

    const textarea = screen.getByRole("textbox", {
      name: "Message",
    });

    fireEvent.change(textarea, {
      target: { value: "continue" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Send" }),
    );

    await waitFor(() =>
      expect(sendMessageMock).toHaveBeenCalledWith(
        "test-token",
        {
          query: "continue",
          conversation_id: conversation.id,
        },
      ),
    );
  });

  it("shows the user message while sending and prevents duplicate sends", async () => {
    let resolveSend!: (value: {
      query: string;
      answer: string;
    }) => void;

    sendMessageMock.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveSend = resolve;
      }),
    );

    renderPage();

    const textarea = screen.getByRole("textbox", {
      name: "Message",
    });

    fireEvent.change(textarea, {
      target: { value: "pending question" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Send" }),
    );

    expect(
      screen.getByText("pending question"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Generating…" }),
    ).toBeDisabled();

    fireEvent.click(
      screen.getByRole("button", { name: "Generating…" }),
    );

    expect(sendMessageMock).toHaveBeenCalledTimes(1);

    resolveSend({
      query: "pending question",
      answer: "generated answer",
    });

    await waitFor(() =>
      expect(sendMessageMock).toHaveBeenCalledTimes(1),
    );
  });

  it("shows the assistant answer after a successful send", async () => {
    getConversationsMock
      .mockResolvedValueOnce({ conversations: [] })
      .mockResolvedValueOnce({
        conversations: [conversation],
      });

    getConversationMessagesMock.mockResolvedValueOnce({
      conversation,
      messages: [
        {
          id: "message-user",
          role: "user",
          content: "hello",
          sequence_number: 1,
          created_at: "2026-01-02T00:00:00Z",
        },
        {
          id: "message-assistant",
          role: "assistant",
          content: "hello answer",
          sequence_number: 2,
          created_at: "2026-01-02T00:01:00Z",
        },
      ],
    });

    renderPage();

    fireEvent.change(
      screen.getByRole("textbox", { name: "Message" }),
      { target: { value: "hello" } },
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Send" }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("hello answer"),
      ).toBeInTheDocument(),
    );

    expect(
      getConversationMessagesMock,
    ).toHaveBeenCalledWith(
      "test-token",
      conversation.id,
    );
  });

  it("restores input and allows retry after send failure", async () => {
    sendMessageMock.mockRejectedValueOnce(
      new Error("send failed"),
    );

    renderPage();

    const textarea = screen.getByRole("textbox", {
      name: "Message",
    });

    fireEvent.change(textarea, {
      target: { value: "retry me" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Send" }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("Unable to send the message."),
      ).toBeInTheDocument(),
    );

    expect(textarea).toHaveValue("retry me");
    expect(
      screen.getByRole("button", { name: "Send" }),
    ).not.toBeDisabled();
  });

  it("reconciles a new conversation and loads its persisted history", async () => {
    const newConversation = {
      id: "33333333-3333-4333-8333-333333333333",
      created_at: "2026-01-03T00:00:00Z",
      updated_at: "2026-01-03T00:00:00Z",
    };

    getConversationsMock
      .mockResolvedValueOnce({ conversations: [] })
      .mockResolvedValueOnce({
        conversations: [newConversation],
      });

    getConversationMessagesMock.mockResolvedValueOnce({
      conversation: newConversation,
      messages: [
        {
          id: "persisted-user",
          role: "user",
          content: "new conversation",
          sequence_number: 1,
          created_at: "2026-01-03T00:00:00Z",
        },
        {
          id: "persisted-assistant",
          role: "assistant",
          content: "persisted answer",
          sequence_number: 2,
          created_at: "2026-01-03T00:01:00Z",
        },
      ],
    });

    renderPage();

    fireEvent.change(
      screen.getByRole("textbox", { name: "Message" }),
      {
        target: { value: "new conversation" },
      },
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Send" }),
    );

    await waitFor(() =>
      expect(
        getConversationsMock,
      ).toHaveBeenCalledTimes(2),
    );

    expect(
      getConversationMessagesMock,
    ).toHaveBeenCalledWith(
      "test-token",
      newConversation.id,
    );

    await waitFor(() =>
      expect(
        screen.getByText("persisted answer"),
      ).toBeInTheDocument(),
    );
  });

  it("does not let stale history overwrite the newly selected conversation", async () => {
    const conversationB = {
      id: "44444444-4444-4444-8444-444444444444",
      created_at: "2026-01-03T00:00:00Z",
      updated_at: "2026-01-03T00:00:00Z",
    };

    let resolveA!: (value: {
      conversation: typeof conversation;
      messages: ConversationMessage[];
    }) => void;

    let resolveB!: (value: {
      conversation: typeof conversationB;
      messages: ConversationMessage[];
    }) => void;

    getConversationsMock.mockResolvedValueOnce({
      conversations: [conversation, conversationB],
    });

    getConversationMessagesMock
      .mockReturnValueOnce(
        new Promise((resolve) => {
          resolveA = resolve;
        }),
      )
      .mockReturnValueOnce(
        new Promise((resolve) => {
          resolveB = resolve;
        }),
      );

    renderPage();

    fireEvent.click(
      await screen.findByRole("button", {
        name: conversation.id,
      }),
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: conversationB.id,
      }),
    );

    resolveA({
      conversation,
      messages: [
        {
          id: "message-a",
          role: "user",
          content: "stale A",
          sequence_number: 1,
          created_at: "2026-01-02T00:00:00Z",
        },
      ],
    });

    await waitFor(() =>
      expect(
        screen.queryByText("stale A"),
      ).not.toBeInTheDocument(),
    );

    resolveB({
      conversation: conversationB,
      messages: [
        {
          id: "message-b",
          role: "user",
          content: "current B",
          sequence_number: 1,
          created_at: "2026-01-03T00:00:00Z",
        },
      ],
    });

    await waitFor(() =>
      expect(
        screen.getByText("current B"),
      ).toBeInTheDocument(),
    );
  });

  it("keeps a sent message when existing-conversation synchronization fails", async () => {
    getConversationsMock.mockResolvedValueOnce({
      conversations: [conversation],
    });

    getConversationMessagesMock
      .mockResolvedValueOnce({
        conversation,
        messages: [],
      })
      .mockRejectedValueOnce(new Error("sync failed"))
      .mockResolvedValueOnce({
        conversation,
        messages: [
          {
            id: "persisted-user",
            role: "user",
            content: "keep me",
            sequence_number: 1,
            created_at: "2026-01-02T00:00:00Z",
          },
          {
            id: "persisted-assistant",
            role: "assistant",
            content: "persisted answer",
            sequence_number: 2,
            created_at: "2026-01-02T00:01:00Z",
          },
        ],
      });

    renderPage();

    fireEvent.click(
      await screen.findByRole("button", {
        name: conversation.id,
      }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("This conversation has no messages yet."),
      ).toBeInTheDocument(),
    );

    fireEvent.change(
      screen.getByRole("textbox", { name: "Message" }),
      {
        target: { value: "keep me" },
      },
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Send" }),
    );

    await waitFor(() =>
      expect(
        screen.getByText(
          "Message sent, but the conversation could not be synchronized.",
        ),
      ).toBeInTheDocument(),
    );

    expect(screen.getByText("keep me")).toBeInTheDocument();
    expect(sendMessageMock).toHaveBeenCalledTimes(1);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Retry synchronization",
      }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("persisted answer"),
      ).toBeInTheDocument(),
    );

    expect(sendMessageMock).toHaveBeenCalledTimes(1);
  });

  it("retries new-conversation synchronization without resending the message", async () => {
    const newConversation = {
      id: "55555555-5555-4555-8555-555555555555",
      created_at: "2026-01-04T00:00:00Z",
      updated_at: "2026-01-04T00:00:00Z",
    };

    getConversationsMock
      .mockResolvedValueOnce({ conversations: [] })
      .mockRejectedValueOnce(new Error("list sync failed"))
      .mockResolvedValueOnce({
        conversations: [newConversation],
      });

    getConversationMessagesMock.mockResolvedValueOnce({
      conversation: newConversation,
      messages: [
        {
          id: "persisted-user",
          role: "user",
          content: "new chat",
          sequence_number: 1,
          created_at: "2026-01-04T00:00:00Z",
        },
        {
          id: "persisted-assistant",
          role: "assistant",
          content: "new persisted answer",
          sequence_number: 2,
          created_at: "2026-01-04T00:01:00Z",
        },
      ],
    });

    renderPage();

    fireEvent.change(
      screen.getByRole("textbox", { name: "Message" }),
      {
        target: { value: "new chat" },
      },
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Send" }),
    );

    await waitFor(() =>
      expect(
        screen.getByRole("button", {
          name: "Retry synchronization",
        }),
      ).toBeInTheDocument(),
    );

    expect(screen.getByText("new chat")).toBeInTheDocument();
    expect(sendMessageMock).toHaveBeenCalledTimes(1);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Retry synchronization",
      }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("new persisted answer"),
      ).toBeInTheDocument(),
    );

    expect(sendMessageMock).toHaveBeenCalledTimes(1);
  });

  it("sends a non-empty message", async () => {
    renderPage();

    const textarea = screen.getByRole("textbox", {
      name: "Message",
    });

    fireEvent.change(textarea, {
      target: { value: "hello" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Send" }),
    );

    await waitFor(() =>
      expect(sendMessageMock).toHaveBeenCalledWith(
        "test-token",
        { query: "hello" },
      ),
    );
  });
});
