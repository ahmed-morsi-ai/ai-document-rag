import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { ConversationHistory } from "../components/ConversationHistory";
import { ConversationList } from "../components/ConversationList";
import { ApiError, conversationApi } from "../services/api";
import type {
  ConversationItem,
  ConversationMessage,
} from "../types/conversations";

export function ChatPage() {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    null,
  );
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isConversationsLoading, setIsConversationsLoading] = useState(true);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [conversationError, setConversationError] = useState("");
  const [historyError, setHistoryError] = useState("");

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
        const response = await conversationApi.getConversationMessages(
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
    setMessages([]);
    setActiveConversationId(conversationId);
  }

  function handleNewConversation() {
    setActiveConversationId(null);
    setMessages([]);
    setHistoryError("");
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
            <h2 id="chat-composer-title" className="visually-hidden">
              Message composer
            </h2>
            <textarea
              aria-label="Message"
              placeholder="Message sending will be available in the next batch."
              disabled
              rows={3}
            />
            <button type="button" disabled>
              Send
            </button>
          </section>
        </section>
      </div>
    </main>
  );
}
