import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import {
  ApiError,
  chatApi,
  conversationApi,
} from "../services/api";
import { ConversationHistory } from "../components/ConversationHistory";
import { ConversationList } from "../components/ConversationList";
import type {
  ConversationItem,
  ConversationMessage,
} from "../types/conversations";

export function ChatPage() {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState<ConversationItem[]>(
    [],
  );
  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isConversationsLoading, setIsConversationsLoading] =
    useState(true);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [conversationError, setConversationError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [sendError, setSendError] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleAuthFailure = useCallback(() => {
    logout();
    navigate("/login", { replace: true });
  }, [logout, navigate]);

  const loadConversations = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsConversationsLoading(true);
    setConversationError("");

    try {
      const response = await conversationApi.getConversations(token);
      setConversations(response.conversations);
    } catch (err) {
      if (
        err instanceof ApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        handleAuthFailure();
        return;
      }

      setConversationError(
        err instanceof ApiError
          ? err.message
          : "Unable to load conversations.",
      );
    } finally {
      setIsConversationsLoading(false);
    }
  }, [handleAuthFailure, token]);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (!token || !activeConversationId) {
      return;
    }

    let cancelled = false;

    const authenticatedToken = token;
    const conversationId = activeConversationId;

    async function loadHistory() {
      setIsHistoryLoading(true);
      setHistoryError("");
      setMessages([]);

      try {
        const response =
          await conversationApi.getConversationMessages(
            authenticatedToken,
            conversationId,
          );

        if (!cancelled) {
          setMessages(response.messages);
        }
      } catch (err) {
        if (cancelled) {
          return;
        }

        if (
          err instanceof ApiError &&
          (err.status === 401 || err.status === 403)
        ) {
          handleAuthFailure();
          return;
        }

        setHistoryError(
          err instanceof ApiError
            ? err.message
            : "Unable to load conversation history.",
        );
      } finally {
        if (!cancelled) {
          setIsHistoryLoading(false);
        }
      }
    }

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [activeConversationId, handleAuthFailure, token]);

  function handleSelectConversation(conversationId: string) {
    if (conversationId === activeConversationId) {
      return;
    }

    setHistoryError("");
    setSendError("");
    setMessages([]);
    setActiveConversationId(conversationId);
  }

  function handleNewConversation() {
    setActiveConversationId(null);
    setMessages([]);
    setHistoryError("");
    setSendError("");
  }

  async function handleSendMessage() {
    const query = inputValue.trim();

    if (!token || !query || isSending) {
      return;
    }

    const existingConversationIds = new Set(
      conversations.map((conversation) => conversation.id),
    );

    const optimisticMessage: ConversationMessage = {
      id: `pending-${Date.now()}`,
      role: "user",
      content: query,
      sequence_number: messages.length + 1,
      created_at: new Date().toISOString(),
    };

    setIsSending(true);
    setSendError("");
    setMessages((current) => [...current, optimisticMessage]);
    setInputValue("");

    try {
      const request =
        activeConversationId === null
          ? { query }
          : {
              query,
              conversation_id: activeConversationId,
            };

      await chatApi.sendMessage(token, request);

      if (activeConversationId !== null) {
        const history =
          await conversationApi.getConversationMessages(
            token,
            activeConversationId,
          );

        setMessages(history.messages);
        return;
      }

      const refreshed =
        await conversationApi.getConversations(token);

      setConversations(refreshed.conversations);

      const newConversations =
        refreshed.conversations.filter(
          (conversation) =>
            !existingConversationIds.has(conversation.id),
        );

      if (newConversations.length !== 1) {
        throw new Error(
          "Unable to synchronize the new conversation.",
        );
      }

      const newConversationId = newConversations[0].id;

      setActiveConversationId(newConversationId);
    } catch (err) {
      setMessages((current) =>
        current.filter(
          (message) => message.id !== optimisticMessage.id,
        ),
      );
      setInputValue(query);

      if (
        err instanceof ApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        handleAuthFailure();
        return;
      }

      setSendError(
        err instanceof ApiError
          ? err.message
          : "Unable to send the message.",
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="chat-page">
      <header className="chat-header">
        <div>
          <p className="eyebrow">AI Document RAG</p>
          <h1>Chat</h1>
          <p className="muted">
            Signed in as <strong>{user?.email}</strong>.
          </p>
        </div>

        <button
          type="button"
          className="secondary"
          onClick={() => {
            logout();
            navigate("/login", { replace: true });
          }}
        >
          Log out
        </button>
      </header>

      <div className="chat-layout">
        <ConversationList
          conversations={conversations}
          activeConversationId={activeConversationId}
          isLoading={isConversationsLoading}
          error={conversationError}
          onSelect={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />

        <section className="chat-main" aria-label="Chat">
          <ConversationHistory
            messages={messages}
            isLoading={isHistoryLoading}
            error={historyError}
            hasActiveConversation={activeConversationId !== null}
          />

          <section
            className="chat-composer"
            aria-labelledby="chat-composer-title"
          >
            <h2
              id="chat-composer-title"
              className="visually-hidden"
            >
              Message composer
            </h2>

            {sendError ? (
              <p role="alert">{sendError}</p>
            ) : null}

            <textarea
              aria-label="Message"
              value={inputValue}
              onChange={(event) => {
                setInputValue(event.target.value);
                setSendError("");
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void handleSendMessage();
                }
              }}
              placeholder="Ask a question about your documents"
              disabled={isSending}
              rows={3}
            />

            <button
              type="button"
              onClick={() => void handleSendMessage()}
              disabled={!inputValue.trim() || isSending}
            >
              {isSending ? "Generating…" : "Send"}
            </button>
          </section>
        </section>
      </div>
    </main>
  );
}
