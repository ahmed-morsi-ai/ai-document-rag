import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { documentsApi } from "../services/documents";
import type { DocumentItem } from "../types/documents";
import {
  ApiError,
  chatApi,
  conversationApi,
} from "../services/api";
import { ConversationHistory } from "../components/ConversationHistory";
import { ConversationList } from "../components/ConversationList";
import type {
  ChatMessage,
  ChatSource,
  ConversationItem,
  ConversationMessage,
} from "../types/conversations";

const CONVERSATION_PAGE_SIZE = 20;
const CONVERSATION_SYNC_PAGE_SIZE = 100;

type PendingSynchronization =
  | {
      kind: "existing";
      conversationId: string;
    }
  | {
      kind: "new";
      existingConversationIds: Set<string>;
    };

function attachSourcesToLatestAssistant(
  messages: ConversationMessage[],
  sources: ChatSource[],
): ChatMessage[] {
  if (sources.length === 0) {
    return messages;
  }

  const assistantIndex = [...messages]
    .map((message, index) => ({ message, index }))
    .reverse()
    .find(({ message }) => message.role === "assistant")
    ?.index;

  if (assistantIndex === undefined) {
    return messages;
  }

  return messages.map((message, index) =>
    index === assistantIndex
      ? { ...message, sources }
      : message,
  );
}

export function ChatPage() {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState<
    ConversationItem[]
  >([]);
  const [totalConversationCount, setTotalConversationCount] =
    useState(0);
  const [currentConversationPage, setCurrentConversationPage] =
    useState(1);
  const conversationPageSize = CONVERSATION_PAGE_SIZE;
  const [conversationSearch, setConversationSearch] = useState("");
  const [conversationSearchInput, setConversationSearchInput] =
    useState("");
  const [activeConversationId, setActiveConversationId] =
    useState<string | null>(null);
  const [messages, setMessages] = useState<
    ChatMessage[]
  >([]);
  const [isConversationsLoading, setIsConversationsLoading] =
    useState(true);
  const [isHistoryLoading, setIsHistoryLoading] =
    useState(false);
  const [conversationError, setConversationError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isDocumentsLoading, setIsDocumentsLoading] = useState(true);
  const [documentError, setDocumentError] = useState("");
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
        await conversationApi.getConversations(token, {
          search: conversationSearch || undefined,
          page: currentConversationPage,
          page_size: conversationPageSize,
        });
      setConversations(response.conversations);
      setTotalConversationCount(response.total_count);
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
  }, [
    conversationPageSize,
    conversationSearch,
    currentConversationPage,
    handleAuthFailure,
    token,
  ]);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  function handleConversationSearchSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setCurrentConversationPage(1);
    setConversationSearch(conversationSearchInput.trim());
  }

  function handlePreviousConversationPage() {
    setCurrentConversationPage((page) => Math.max(1, page - 1));
  }

  function handleNextConversationPage() {
    if (
      currentConversationPage * conversationPageSize <
      totalConversationCount
    ) {
      setCurrentConversationPage((page) => page + 1);
    }
  }

  useEffect(() => {
    if (!token) {
      return;
    }

    const authenticatedToken = token;
    let cancelled = false;

    async function loadDocuments() {
      setIsDocumentsLoading(true);
      setDocumentError("");

      try {
        const loadedDocuments =
          await documentsApi.list(authenticatedToken);

        if (cancelled) {
          return;
        }

        setDocuments(loadedDocuments);
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

        setDocumentError(
          err instanceof ApiError
            ? err.message
            : "Unable to load document availability.",
        );
      } finally {
        if (!cancelled) {
          setIsDocumentsLoading(false);
        }
      }
    }

    void loadDocuments();

    return () => {
      cancelled = true;
    };
  }, [handleAuthFailure, token]);

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

  async function handleRetryDocuments() {
    if (!token || isDocumentsLoading) {
      return;
    }

    setIsDocumentsLoading(true);
    setDocumentError("");

    try {
      const loadedDocuments = await documentsApi.list(token);
      setDocuments(loadedDocuments);
    } catch (err) {
      if (
        err instanceof ApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        handleAuthFailure();
        return;
      }

      setDocumentError(
        err instanceof ApiError
          ? err.message
          : "Unable to load document availability.",
      );
    } finally {
      setIsDocumentsLoading(false);
    }
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

      const remainingCount = Math.max(
        totalConversationCount - 1,
        0,
      );
      const lastValidPage = Math.max(
        1,
        Math.ceil(remainingCount / conversationPageSize),
      );

      setTotalConversationCount(remainingCount);
      setDeleteTargetConversationId(null);

      if (currentConversationPage > lastValidPage) {
        setCurrentConversationPage(lastValidPage);
      } else {
        await loadConversations();
      }

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
    sources: ChatSource[] = [],
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

      setMessages(
        attachSourcesToLatestAssistant(history.messages, sources),
      );
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
    sources: ChatSource[] = [],
  ) {
    if (operationId !== chatOperationRef.current) {
      return;
    }

    try {
      const refreshed =
        await conversationApi.getConversations(
          token as string,
          {
            page: 1,
            page_size: CONVERSATION_SYNC_PAGE_SIZE,
          },
        );

      if (operationId !== chatOperationRef.current) {
        return;
      }

      const newConversations =
        refreshed.conversations.filter(
          (conversation) =>
            !existingConversationIds.has(conversation.id),
        );

      setConversations((current) =>
        newConversations.length > 0
          ? [
              ...newConversations,
              ...current.filter(
                (conversation) =>
                  !newConversations.some(
                    (newConversation) =>
                      newConversation.id === conversation.id,
                  ),
              ),
            ].slice(0, conversationPageSize)
          : current,
      );

      if (newConversations.length !== 1) {
        throw new Error(
          "Unable to synchronize the new conversation.",
        );
      }

      setTotalConversationCount(refreshed.total_count);

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

      setMessages(
        attachSourcesToLatestAssistant(history.messages, sources),
      );
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

      const chatResponse = await chatApi.sendMessage(
        token,
        request,
      );

      if (operationId !== chatOperationRef.current) {
        return;
      }

      setIsSending(false);

      if (activeConversationId !== null) {
        await synchronizeExistingConversation(
          operationId,
          activeConversationId,
          chatResponse.sources,
        );
        return;
      }

      await synchronizeNewConversation(
        operationId,
        existingConversationIds,
        chatResponse.sources,
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

  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  return (
    <div className="chat-page">
      <section className="chat-workspace">
        <div className="chat-workspace-main">
        <ConversationList
          conversations={conversations}
          totalCount={totalConversationCount}
          currentPage={currentConversationPage}
          pageSize={conversationPageSize}
          search={conversationSearch}
          searchInput={conversationSearchInput}
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
          onSearchInputChange={setConversationSearchInput}
          onSearchSubmit={handleConversationSearchSubmit}
          onPreviousPage={handlePreviousConversationPage}
          onNextPage={handleNextConversationPage}
        />

        <section className="chat-main" aria-label="Chat conversation">
          <header className="chat-conversation-header">
            <div className="chat-conversation-heading">
              <p className="workspace-section-kicker">Conversation</p>
              <h1>
                {activeConversation?.title ||
                  (activeConversationId
                    ? "Untitled conversation"
                    : "New conversation")}
              </h1>
              <p>
                {user?.email}
              </p>
            </div>

            <div className="chat-header-actions">
              <div className="chat-header-context">
                <span className="chat-context-dot" aria-hidden="true" />
                {isDocumentsLoading ? (
                  <span role="status">
                    Loading document availability…
                  </span>
                ) : documentError ? (
                  <span>Document context unavailable</span>
                ) : documents.length === 0 ? (
                  <span>No documents available</span>
                ) : (
                  <span>
                    {documents.length}{" "}
                    {documents.length === 1
                      ? "document"
                      : "documents"}{" "}
                    available
                  </span>
                )}
              </div>

              <button
                type="button"
                className="secondary chat-logout-button"
                onClick={() => {
                  invalidateChatOperation();
                  logout();
                  navigate("/login", { replace: true });
                }}
              >
                Log out
              </button>
            </div>
          </header>

          <section
            className="chat-context-panel"
            aria-labelledby="document-context-title"
          >
            <div>
              <p className="workspace-section-kicker">
                Document context
              </p>
              <h2 id="document-context-title">
                Available workspace context
              </h2>

              {isDocumentsLoading ? (
                <p role="status">
                  Checking available documents…
                </p>
              ) : documentError ? (
                <div className="chat-context-inline-error">
                  <p role="alert">{documentError}</p>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => void handleRetryDocuments()}
                  >
                    Retry
                  </button>
                </div>
              ) : documents.length === 0 ? (
                <div className="chat-context-empty">
                  <p>No documents available.</p>
                  <span>
                    Upload a document from the Dashboard to add
                    workspace context.
                  </span>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => navigate("/app")}
                  >
                    Upload a document
                  </button>
                </div>
              ) : (
                <div className="chat-context-available">
                  <p>
                    {documents.length}{" "}
                    {documents.length === 1 ? "document" : "documents"}{" "}
                    available for your workspace.
                  </p>
                  <span>
                    Your chat can use the documents currently available
                    in this workspace.
                  </span>
                </div>
              )}
            </div>
          </section>

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
              <div className="chat-send-error" role="alert">
                <span>{sendError}</span>

                {pendingSynchronization ? (
                  <button
                    type="button"
                    className="secondary"
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

            <div className="chat-composer-surface">
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
                placeholder="Ask something about your documents…"
                disabled={isSending}
                rows={3}
              />

              <div className="chat-composer-footer">
                <span>
                  Enter to send · Shift+Enter for a new line
                </span>

                <button
                  type="button"
                  className="primary chat-send-button"
                  onClick={() => void handleSendMessage()}
                  disabled={
                    !inputValue.trim() || isSending
                  }
                >
                  {isSending ? "Generating…" : "Send"}
                </button>
              </div>
            </div>
          </section>
        </section>
      </div>
    </section>
  </div>
  );
}
