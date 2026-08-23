import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
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

type PendingSynchronization =
  | {
      kind: "existing";
      conversationId: string;
    }
  | {
      kind: "new";
      existingConversationIds: Set<string>;
    };

export function ChatPage() {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState<
    ConversationItem[]
  >([]);
  const [activeConversationId, setActiveConversationId] =
    useState<string | null>(null);
  const [messages, setMessages] = useState<
    ConversationMessage[]
  >([]);
  const [isConversationsLoading, setIsConversationsLoading] =
    useState(true);
  const [isHistoryLoading, setIsHistoryLoading] =
    useState(false);
  const [conversationError, setConversationError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [sendError, setSendError] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [pendingSynchronization, setPendingSynchronization] =
    useState<PendingSynchronization | null>(null);
  const [deleteTargetConversationId, setDeleteTargetConversationId] =
    useState<string | null>(null);
  const [deletingConversationId, setDeletingConversationId] =
    useState<string | null>(null);
  const [deleteError, setDeleteError] = useState("");

  const chatOperationRef = useRef(0);
  const skipNextHistoryLoadRef = useRef<string | null>(null);
  const historyRequestRef = useRef(0);

  const handleAuthFailure = useCallback(() => {
    chatOperationRef.current += 1;
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
      const response =
        await conversationApi.getConversations(token);
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

    if (
      skipNextHistoryLoadRef.current === activeConversationId
    ) {
      skipNextHistoryLoadRef.current = null;
      return;
    }

    let cancelled = false;
    const historyRequestId = ++historyRequestRef.current;

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

        if (
          !cancelled &&
          historyRequestId === historyRequestRef.current
        ) {
          setMessages(response.messages);
        }
      } catch (err) {
        if (
          cancelled ||
          historyRequestId !== historyRequestRef.current
        ) {
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
        if (
          !cancelled &&
          historyRequestId === historyRequestRef.current
        ) {
          setIsHistoryLoading(false);
        }
      }
    }

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [activeConversationId, handleAuthFailure, token]);

  function invalidateChatOperation() {
    chatOperationRef.current += 1;
    setIsSending(false);
  }

  function handleSelectConversation(conversationId: string) {
    if (conversationId === activeConversationId) {
      return;
    }

    invalidateChatOperation();
    setPendingSynchronization(null);
    setHistoryError("");
    setSendError("");
    setMessages([]);
    setInputValue("");
    setActiveConversationId(conversationId);
  }

  function handleNewConversation() {
    invalidateChatOperation();
    setPendingSynchronization(null);
    setActiveConversationId(null);
    setMessages([]);
    setHistoryError("");
    setSendError("");
    setInputValue("");
  }

  function handleDeleteRequest(conversationId: string) {
    if (
      deleteTargetConversationId !== null ||
      deletingConversationId !== null
    ) {
      return;
    }

    setDeleteError("");
    setDeleteTargetConversationId(conversationId);
  }

  function handleDeleteCancel() {
    setDeleteError("");
    setDeleteTargetConversationId(null);
  }

  async function handleDeleteConfirm(conversationId: string) {
    if (!token || deleteTargetConversationId !== conversationId) {
      return;
    }

    setDeleteError("");
    setDeletingConversationId(conversationId);
    setDeleteTargetConversationId(null);

    try {
      await conversationApi.deleteConversation(
        token,
        conversationId,
      );

      setConversations((current) =>
        current.filter(
          (conversation) => conversation.id !== conversationId,
        ),
      );

      setDeletingConversationId(null);

      if (activeConversationId === conversationId) {
        historyRequestRef.current += 1;
        invalidateChatOperation();
        setPendingSynchronization(null);
        setActiveConversationId(null);
        setMessages([]);
        setHistoryError("");
        setSendError("");
        setInputValue("");
      }
    } catch (err) {
      if (
        err instanceof ApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        setDeletingConversationId(null);
        setDeleteTargetConversationId(null);
        handleAuthFailure();
        return;
      }

      setDeletingConversationId(null);
      setDeleteTargetConversationId(null);
      setDeleteError(
        err instanceof ApiError
          ? err.message
          : "Unable to delete conversation.",
      );
    }
  }

  async function synchronizeExistingConversation(
    operationId: number,
    conversationId: string,
  ) {
    if (operationId !== chatOperationRef.current) {
      return;
    }

    try {
      const history =
        await conversationApi.getConversationMessages(
          token as string,
          conversationId,
        );

      if (operationId !== chatOperationRef.current) {
        return;
      }

      setMessages(history.messages);
      setPendingSynchronization(null);
      setSendError("");
    } catch (err) {
      if (operationId !== chatOperationRef.current) {
        return;
      }

      if (
        err instanceof ApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        handleAuthFailure();
        return;
      }

      setPendingSynchronization({
        kind: "existing",
        conversationId,
      });
      setSendError(
        "Message sent, but the conversation could not be synchronized.",
      );
    }
  }

  async function synchronizeNewConversation(
    operationId: number,
    existingConversationIds: Set<string>,
  ) {
    if (operationId !== chatOperationRef.current) {
      return;
    }

    try {
      const refreshed =
        await conversationApi.getConversations(
          token as string,
        );

      if (operationId !== chatOperationRef.current) {
        return;
      }

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

      skipNextHistoryLoadRef.current = newConversationId;
      setActiveConversationId(newConversationId);

      const history =
        await conversationApi.getConversationMessages(
          token as string,
          newConversationId,
        );

      if (operationId !== chatOperationRef.current) {
        return;
      }

      setMessages(history.messages);
      setPendingSynchronization(null);
      setSendError("");
    } catch (err) {
      if (operationId !== chatOperationRef.current) {
        return;
      }

      if (
        err instanceof ApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        handleAuthFailure();
        return;
      }

      setPendingSynchronization({
        kind: "new",
        existingConversationIds,
      });
      setSendError(
        "Message sent, but the new conversation could not be synchronized.",
      );
    }
  }

  async function handleRetrySynchronization() {
    if (!token || !pendingSynchronization || isSending) {
      return;
    }

    const operationId = ++chatOperationRef.current;
    setSendError("");

    if (pendingSynchronization.kind === "existing") {
      await synchronizeExistingConversation(
        operationId,
        pendingSynchronization.conversationId,
      );
      return;
    }

    await synchronizeNewConversation(
      operationId,
      pendingSynchronization.existingConversationIds,
    );
  }

  async function handleSendMessage() {
    const query = inputValue.trim();

    if (!token || !query || isSending) {
      return;
    }

    historyRequestRef.current += 1;
    const operationId = ++chatOperationRef.current;
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
    setPendingSynchronization(null);
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

      if (operationId !== chatOperationRef.current) {
        return;
      }

      setIsSending(false);

      if (activeConversationId !== null) {
        await synchronizeExistingConversation(
          operationId,
          activeConversationId,
        );
        return;
      }

      await synchronizeNewConversation(
        operationId,
        existingConversationIds,
      );
    } catch (err) {
      if (operationId !== chatOperationRef.current) {
        return;
      }

      setIsSending(false);
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
            invalidateChatOperation();
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
          deleteTargetConversationId={deleteTargetConversationId}
          deletingConversationId={deletingConversationId}
          deleteError={deleteError}
          onSelect={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteRequest={handleDeleteRequest}
          onDeleteCancel={handleDeleteCancel}
          onDeleteConfirm={handleDeleteConfirm}
        />

        <section className="chat-main" aria-label="Chat">
          <ConversationHistory
            messages={messages}
            isLoading={isHistoryLoading}
            error={historyError}
            hasActiveConversation={
              activeConversationId !== null
            }
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
              <div>
                <p role="alert">{sendError}</p>

                {pendingSynchronization ? (
                  <button
                    type="button"
                    onClick={() =>
                      void handleRetrySynchronization()
                    }
                    disabled={isSending}
                  >
                    Retry synchronization
                  </button>
                ) : null}
              </div>
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
